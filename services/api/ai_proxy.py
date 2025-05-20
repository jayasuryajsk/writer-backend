import sqlite3
import json
import time
from difflib import unified_diff
from typing import Dict, Any
import openai

DB_PATH = 'ai_usage.db'
RATE_LIMIT = 50000  # tokens per 24h per user


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "CREATE TABLE IF NOT EXISTS usage (user TEXT, tokens INTEGER, ts REAL)"
    )
    conn.commit()
    conn.close()


def get_usage(user: str) -> int:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    day_ago = time.time() - 86400
    c.execute(
        "SELECT SUM(tokens) FROM usage WHERE user=? AND ts>?",
        (user, day_ago),
    )
    result = c.fetchone()[0]
    conn.close()
    return int(result or 0)


def add_usage(user: str, tokens: int) -> None:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO usage (user, tokens, ts) VALUES (?, ?, ?)",
        (user, tokens, time.time()),
    )
    conn.commit()
    conn.close()


def token_count(payload: Dict[str, Any]) -> int:
    return len(json.dumps(payload)) // 4 or 1


def check_quota(user: str, tokens: int):
    used = get_usage(user)
    if used + tokens > RATE_LIMIT:
        raise ValueError("quota exceeded")
    add_usage(user, tokens)


def completions(payload: Dict[str, Any], user: str):
    tokens = token_count(payload)
    check_quota(user, tokens)
    return openai.ChatCompletion.create(**payload)


def edit_predictions(before: str, instruction: str, user: str) -> Dict[str, str]:
    prompt = f"Apply instruction to text.\nInstruction:\n{instruction}\nText:\n{before}\nResult:"
    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "model": "gpt-3.5-turbo",
    }
    tokens = token_count(payload)
    check_quota(user, tokens)
    result = openai.ChatCompletion.create(**payload)
    after = result["choices"][0]["message"]["content"]
    diff = "\n".join(
        unified_diff(before.splitlines(), after.splitlines(), fromfile="before", tofile="after")
    )
    return {"diff": diff}
