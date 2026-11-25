"""Load Google credentials from the private folder (GOOGLE_PRIVATE_DIR).

The server never opens a browser. If the token is missing or lacks the
needed permissions, run `uv run authorize.py` once.
"""

import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar",
]


def private_dir() -> Path:
    value = os.environ.get("GOOGLE_PRIVATE_DIR")
    if not value:
        raise RuntimeError("GOOGLE_PRIVATE_DIR is not set (it must point to a folder).")
    path = Path(value)
    if not path.is_dir():
        raise RuntimeError(f"GOOGLE_PRIVATE_DIR is not a folder: {path}")
    return path


def find_client_file(folder: Path) -> Path:
    preferred = folder / "client_secret.json"
    if preferred.exists():
        return preferred
    matches = sorted(folder.glob("client_secret*.json"))
    if not matches:
        raise RuntimeError(f"No client_secret*.json in {folder}")
    return matches[0]


def load_credentials() -> Credentials:
    token_path = private_dir() / "token.json"
    if not token_path.exists():
        raise RuntimeError("token.json not found. Run: uv run authorize.py")
    creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if not creds.has_scopes(SCOPES):
        raise RuntimeError("token.json lacks permissions. Run: uv run authorize.py")
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            token_path.write_text(creds.to_json(), encoding="utf-8")
        else:
            raise RuntimeError("token.json is invalid. Run: uv run authorize.py")
    return creds
