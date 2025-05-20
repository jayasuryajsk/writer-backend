import os
import json
import unittest
import asyncio
from fastapi import HTTPException
from starlette.requests import Request
from services.api.rpc import rpc_redirect, liveblocks_auth, encode_jwt, _b64url_encode

SECRET = b'supersecret'
JWK = json.dumps({"kty": "oct", "k": _b64url_encode(SECRET)})
os.environ['SUPABASE_JWK'] = JWK
os.environ['LIVEBLOCKS_SECRET_KEY'] = 'live-secret'
os.environ['DOMAIN'] = 'example.com'


def make_supabase_token(uid: str = 'user1') -> str:
    return encode_jwt({"sub": uid}, SECRET)


def make_request(method: str, path: str, headers: dict = None, json_body=None):
    headers = headers or {}
    bheaders = [(k.lower().encode(), v.encode()) for k, v in headers.items()]
    scope = {
        'type': 'http',
        'method': method,
        'path': path,
        'headers': bheaders,
    }
    async def receive():
        if json_body is None:
            return {'type': 'http.request', 'body': b'', 'more_body': False}
        body = json.dumps(json_body).encode()
        return {'type': 'http.request', 'body': body, 'more_body': False}
    return Request(scope, receive)


class RpcTestCase(unittest.TestCase):
    def test_rpc_valid_creds_redirect(self):
        token = make_supabase_token()
        req = make_request('GET', '/rpc', headers={'Authorization': f'user1 {token}'})
        resp = asyncio.run(rpc_redirect(req))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.headers['location'], 'wss://collab.example.com/rpc')

    def test_rpc_invalid_creds(self):
        req = make_request('GET', '/rpc', headers={'Authorization': 'user1 badtoken'})
        with self.assertRaises(HTTPException) as cm:
            asyncio.run(rpc_redirect(req))
        self.assertEqual(cm.exception.status_code, 401)

    def test_liveblocks_auth_valid(self):
        token = make_supabase_token()
        req = make_request('POST', '/liveblocks/auth', headers={'Authorization': token}, json_body={'roomId': 'room1'})
        resp = asyncio.run(liveblocks_auth(req))
        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.body)
        self.assertIn('token', body)

    def test_liveblocks_auth_invalid(self):
        req = make_request('POST', '/liveblocks/auth', headers={'Authorization': 'badtoken'}, json_body={'roomId': 'room1'})
        with self.assertRaises(HTTPException) as cm:
            asyncio.run(liveblocks_auth(req))
        self.assertEqual(cm.exception.status_code, 401)


if __name__ == '__main__':
    unittest.main()
