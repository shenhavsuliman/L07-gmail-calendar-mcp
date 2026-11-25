"""MCP server "gmail-calendar": Gmail + Google Calendar tools (stdio).

There is NO tool that sends or deletes anything. The agent prepares, the human sends.
Never print to stdout here: stdout is the MCP channel.
"""

import base64
from datetime import datetime, timedelta
from email.message import EmailMessage
from zoneinfo import ZoneInfo

from googleapiclient.discovery import build
from mcp.server.fastmcp import FastMCP

from google_auth import load_credentials

TZ = ZoneInfo("Asia/Jerusalem")
mcp = FastMCP("gmail-calendar")


def gmail():
    return build("gmail", "v1", credentials=load_credentials(), cache_discovery=False)


def calendar():
    return build("calendar", "v3", credentials=load_credentials(), cache_discovery=False)


@mcp.tool()
def search_emails(query: str, max_results: int = 10) -> list[dict]:
    """Search Gmail messages using Gmail search syntax (e.g. 'from:dana meeting').
    Returns id, sender, subject, date and a short snippet. Read-only."""
    svc = gmail()
    found = svc.users().messages().list(
        userId="me", q=query, maxResults=max_results).execute().get("messages", [])
    results = []
    for m in found:
        msg = svc.users().messages().get(
            userId="me", id=m["id"], format="metadata",
            metadataHeaders=["From", "Subject", "Date"]).execute()
        h = {x["name"]: x["value"] for x in msg["payload"].get("headers", [])}
        results.append({"id": m["id"], "from": h.get("From"), "subject": h.get("Subject"),
                        "date": h.get("Date"), "snippet": msg.get("snippet", "")})
    return results


def _body_text(payload: dict) -> str:
    if payload.get("mimeType") == "text/plain" and payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", "replace")
    for part in payload.get("parts", []) or []:
        text = _body_text(part)
        if text:
            return text
    return ""


@mcp.tool()
def read_email(message_id: str) -> dict:
    """Read one Gmail message by id: sender, subject, date and plain-text body. Read-only."""
    msg = gmail().users().messages().get(userId="me", id=message_id, format="full").execute()
    h = {x["name"]: x["value"] for x in msg["payload"].get("headers", [])}
    return {"from": h.get("From"), "subject": h.get("Subject"), "date": h.get("Date"),
            "body": _body_text(msg["payload"])[:5000]}


@mcp.tool()
def create_draft(to: str, subject: str, body: str) -> str:
    """Create a Gmail DRAFT. Does NOT send. The user reviews and sends it from Gmail."""
    msg = EmailMessage()
    msg["To"], msg["Subject"] = to, subject
    msg.set_content(body)
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    draft = gmail().users().drafts().create(
        userId="me", body={"message": {"raw": raw}}).execute()
    return f"Draft created (id {draft['id']}). It was NOT sent."


@mcp.tool()
def list_events(days_ahead: int = 1) -> list[dict]:
    """List events in the primary calendar from now until N days ahead. Read-only."""
    now = datetime.now(TZ)
    items = calendar().events().list(
        calendarId="primary", timeMin=now.isoformat(),
        timeMax=(now + timedelta(days=days_ahead)).isoformat(),
        singleEvents=True, orderBy="startTime").execute().get("items", [])
    return [{"title": e.get("summary"), "start": e["start"].get("dateTime", e["start"].get("date")),
             "end": e["end"].get("dateTime", e["end"].get("date"))} for e in items]


@mcp.tool()
def find_free_slots(date: str, duration_minutes: int = 60,
                    day_start: str = "09:00", day_end: str = "17:00") -> list[str]:
    """Find free time slots on a date (YYYY-MM-DD) between day_start and day_end
    (HH:MM, Israel time) that fit duration_minutes. Read-only."""
    start = datetime.fromisoformat(f"{date}T{day_start}").replace(tzinfo=TZ)
    end = datetime.fromisoformat(f"{date}T{day_end}").replace(tzinfo=TZ)
    busy = calendar().freebusy().query(body={
        "timeMin": start.isoformat(), "timeMax": end.isoformat(), "timeZone": "Asia/Jerusalem",
        "items": [{"id": "primary"}]}).execute()["calendars"]["primary"]["busy"]
    slots, cursor, need = [], start, timedelta(minutes=duration_minutes)
    for b in busy:
        b_start = datetime.fromisoformat(b["start"]).astimezone(TZ)
        b_end = datetime.fromisoformat(b["end"]).astimezone(TZ)
        if b_start - cursor >= need:
            slots.append(f"{cursor:%H:%M}-{b_start:%H:%M}")
        cursor = max(cursor, b_end)
    if end - cursor >= need:
        slots.append(f"{cursor:%H:%M}-{end:%H:%M}")
    return slots


@mcp.tool()
def create_event(title: str, start: str, end: str, description: str = "") -> str:
    """Create an event in the primary calendar. start/end are ISO date-times
    (e.g. 2026-11-25T18:30), interpreted in Israel time. Does not invite anyone."""
    def iso(s: str) -> str:
        dt = datetime.fromisoformat(s)
        return (dt if dt.tzinfo else dt.replace(tzinfo=TZ)).isoformat()
    event = calendar().events().insert(calendarId="primary", body={
        "summary": title, "description": description,
        "start": {"dateTime": iso(start)}, "end": {"dateTime": iso(end)}}).execute()
    return f"Event created: {title} ({event['start']['dateTime']})"


if __name__ == "__main__":
    mcp.run(transport="stdio")
