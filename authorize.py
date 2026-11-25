"""One-time sign-in: creates token.json with the permissions the server needs.

Run once (opens a browser):  uv run authorize.py
"""

from google_auth_oauthlib.flow import InstalledAppFlow

from google_auth import SCOPES, find_client_file, private_dir


def main() -> None:
    folder = private_dir()
    flow = InstalledAppFlow.from_client_secrets_file(str(find_client_file(folder)), SCOPES)
    creds = flow.run_local_server(port=0)
    (folder / "token.json").write_text(creds.to_json(), encoding="utf-8")
    print(f"Token saved to: {folder / 'token.json'}")


if __name__ == "__main__":
    main()
