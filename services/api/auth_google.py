import os
import uuid
from base64 import b64encode
from urllib import request
from typing import Dict, Tuple

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse

router = APIRouter()

# In-memory state storage
_STATE_DB: Dict[str, Tuple[str, str]] = {}

# Supabase client is injected for easier testing
supabase_client = None


def rsa_encrypt(message: str, pubkey: str) -> str:
    """Placeholder RSA encryption using base64 encoding."""
    return b64encode(message.encode()).decode()


def get_state_db() -> Dict[str, Tuple[str, str]]:
    return _STATE_DB


def get_supabase_client():
    if supabase_client is None:
        raise HTTPException(status_code=500, detail="Supabase client not configured")
    return supabase_client


@router.get("/native_app_signin")
def native_app_signin(callback_port: str, pubkey: str, state_db: Dict[str, Tuple[str, str]] = Depends(get_state_db)):
    state = str(uuid.uuid4())
    state_db[state] = (callback_port, pubkey)

    supabase_url = os.getenv("SUPABASE_URL", "https://supabase.example.com")
    domain = os.getenv("DOMAIN", "example.com")
    redirect_to = f"https://api.{domain}/oauth/callback"
    url = (
        f"{supabase_url}/auth/v1/authorize?provider=google&state={state}&redirect_to={redirect_to}"
    )
    return RedirectResponse(url)


@router.get("/oauth/callback")
def oauth_callback(code: str, state: str, state_db: Dict[str, Tuple[str, str]] = Depends(get_state_db), client=Depends(get_supabase_client)):
    if state not in state_db:
        raise HTTPException(status_code=400, detail="Invalid state")
    callback_port, pubkey = state_db.pop(state)

    session = client.auth.exchange_code_for_session(code)
    supabase_uid = session.user.id
    access_token = session.session.access_token

    encrypted = rsa_encrypt(f"{supabase_uid} {access_token}", pubkey)

    url = f"http://127.0.0.1:{callback_port}/token?data={encrypted}"
    try:
        request.urlopen(url)
    except Exception:
        # ignore connection errors during callback
        pass
    return RedirectResponse("/native_app_signin_succeeded")

