import os
import json
import base64
import hmac
import hashlib
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse

app = FastAPI()


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(data: str) -> bytes:
    padding = '=' * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _jwt_signing_input(header: dict, payload: dict) -> bytes:
    header_b64 = _b64url_encode(json.dumps(header, separators=(',', ':')).encode())
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(',', ':')).encode())
    return f"{header_b64}.{payload_b64}".encode(), header_b64, payload_b64


def encode_jwt(payload: dict, secret: bytes) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    signing_input, header_b64, payload_b64 = _jwt_signing_input(header, payload)
    signature = hmac.new(secret, signing_input, hashlib.sha256).digest()
    return f"{header_b64}.{payload_b64}.{_b64url_encode(signature)}"


def decode_jwt(token: str, secret: bytes) -> dict:
    parts = token.split('.')
    if len(parts) != 3:
        raise ValueError('Invalid token')
    header_b64, payload_b64, sig_b64 = parts
    signing_input = f"{header_b64}.{payload_b64}".encode()
    signature = _b64url_decode(sig_b64)
    expected = hmac.new(secret, signing_input, hashlib.sha256).digest()
    if not hmac.compare_digest(signature, expected):
        raise ValueError('Invalid signature')
    payload = json.loads(_b64url_decode(payload_b64))
    return payload


def _get_supabase_secret() -> bytes:
    jwk_json = os.environ.get('SUPABASE_JWK')
    if not jwk_json:
        raise RuntimeError('SUPABASE_JWK not configured')
    jwk = json.loads(jwk_json)
    if jwk.get('kty') != 'oct' or 'k' not in jwk:
        raise RuntimeError('Unsupported JWK')
    return _b64url_decode(jwk['k'])


def verify_supabase_jwt(token: str):
    secret = _get_supabase_secret()
    return decode_jwt(token, secret)


@app.get('/rpc')
async def rpc_redirect(request: Request):
    auth = request.headers.get('Authorization', '')
    try:
        _uid, token = auth.split(' ', 1)
    except ValueError:
        raise HTTPException(status_code=401)
    try:
        verify_supabase_jwt(token)
    except Exception:
        raise HTTPException(status_code=401)
    domain = os.environ.get('DOMAIN', 'localhost')
    location = f"wss://collab.{domain}/rpc"
    return RedirectResponse(location, status_code=302)


@app.post('/liveblocks/auth')
async def liveblocks_auth(request: Request):
    auth = request.headers.get('Authorization', '')
    if not auth:
        raise HTTPException(status_code=401)
    token = auth.split(' ', 1)[-1]
    try:
        verify_supabase_jwt(token)
    except Exception:
        raise HTTPException(status_code=401)
    data = await request.json()
    room_id = data.get('roomId') if isinstance(data, dict) else None
    if not room_id:
        raise HTTPException(status_code=400)
    secret = os.environ.get('LIVEBLOCKS_SECRET_KEY')
    if not secret:
        raise RuntimeError('LIVEBLOCKS_SECRET_KEY not configured')
    live_token = encode_jwt({'roomId': room_id}, secret.encode())
    return JSONResponse({"token": live_token})


# expose app for ASGI servers
application = app
