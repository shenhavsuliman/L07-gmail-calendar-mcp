# L07 – gmail-calendar MCP server

An MCP server (Python, FastMCP, stdio) that gives an AI agent six Gmail and
Google Calendar tools. **There is no tool that sends or deletes anything.**

| Tool | Google API call |
|---|---|
| search_emails(query, max_results) | gmail users.messages.list |
| read_email(message_id) | gmail users.messages.get |
| create_draft(to, subject, body) – draft only | gmail users.drafts.create |
| list_events(days_ahead) | calendar events.list |
| find_free_slots(date, duration_minutes) | calendar freebusy.query |
| create_event(title, start, end, description) | calendar events.insert |

Time zone: Asia/Jerusalem.

## Secrets (never in this folder)

`GOOGLE_PRIVATE_DIR` points to the private folder (here `C:\secrets`) that holds
`client_secret.json` and `token.json`. The server reads them but never copies or prints them.

## Setup

```powershell
python -m uv sync
$env:GOOGLE_PRIVATE_DIR = "C:\secrets"
python -m uv run authorize.py      # one time: sign in, creates token.json
python -m uv run test_server.py    # self-test: lists tools, calls list_events
```

## Register in Claude Code

```powershell
claude mcp add gmail-calendar --transport stdio -e GOOGLE_PRIVATE_DIR=C:\secrets '--' python -m uv run --directory "<this folder>" server.py
```

Then restart `claude` and type `/mcp` – `gmail-calendar` should be connected with 6 tools.

## Prompts used in Claude Code

1. `What do I have in my calendar tomorrow? Use the gmail-calendar MCP tools.`
2. `Write a Gmail draft to myself with the subject "L06 test" and add a calendar event for today, 4 hours from now, called "MCP works". Use the gmail-calendar MCP tools.`
3. `Find a free hour tomorrow between 09:00 and 17:00 and add an event called "Study group" there. Use the gmail-calendar MCP tools.`
4. `Now send the "L06 test" draft.` – the agent answered that the server has no send tool (boundary works).
   It then offered to send via the browser instead – declined: the human sends.
