# PRD – gmail-calendar MCP server

**Product:** gmail-calendar – an MCP server that lets an AI agent work with Gmail and Google Calendar
**Owner:** @shenhavsuliman (individual project, approved by the lecturer)
**Course:** AI Agents and Vibe Coding, Lesson 06
**Status:** Implemented and tested

---

## 1. Problem

In Lesson 05 the agent wrote a fixed program (`gmail_calendar_test.py`) that does exactly one thing:
create a draft and add an event four hours from now. Every new request ("find a free hour",
"search my email") needs a new prompt and a new program, and the program cannot check
whether the calendar is busy.

We want to talk to the agent in free language and let it choose the right action by itself –
without writing new code for each request, and without giving it the power to do damage.

## 2. Goal

Build a small tool server (MCP) that exposes Gmail and Calendar actions as tools.
Any MCP-capable agent (Claude Code, Antigravity, Codex…) can connect to it, read the tool menu,
and pick the tools it needs for a request.

**Success =** one free-language request creates a Gmail draft and a calendar event
through the server's tools, with no new program written.

## 3. Users

| User | Situation |
|---|---|
| Student (me) | Works in Claude Code in a terminal; wants the agent to handle mail and calendar tasks |
| Lecturer | Reviews the repository, the screenshots and the reflection |
| Anyone cloning the repo | Runs the same server against their own Google account |

## 4. Functional requirements

The server exposes **exactly six tools**, each with a short, clear English description
(the model chooses tools by their description):

| # | Tool | What it does | Google API |
|---|---|---|---|
| F1 | `search_emails(query, max_results)` | Search messages (Gmail search syntax). Read-only | `users.messages.list` + `get` |
| F2 | `read_email(message_id)` | Return sender, subject, date and plain-text body. Read-only | `users.messages.get` |
| F3 | `create_draft(to, subject, body)` | Create a **draft only** – never sends | `users.drafts.create` |
| F4 | `list_events(days_ahead)` | Upcoming events in the primary calendar. Read-only | `events.list` |
| F5 | `find_free_slots(date, duration_minutes)` | Free slots between 09:00–17:00 on a date. Read-only | `freebusy.query` |
| F6 | `create_event(title, start, end, description)` | Create an event, invites no one | `events.insert` |

- **F7** – All times use the **Asia/Jerusalem** time zone.
- **F8** – The server runs locally with **stdio** transport and is started by the agent itself.

## 5. Out of scope (deliberately)

| Not included | Why |
|---|---|
| Sending email (`users.messages.send`, `drafts.send`) | The agent prepares, the human reviews and sends |
| Deleting mail or events | No irreversible actions through the agent |
| Forwarding mail, managing labels, inviting guests | Not needed – fewer tools = fewer risks and fewer tokens |
| HTTP / remote access for web apps | Local use only in this lesson |

## 6. Security and privacy

- **Secrets stay outside the project:** `client_secret.json` and `token.json` live in a private
  folder (`C:\secrets`), whose path comes from the environment variable `GOOGLE_PRIVATE_DIR`.
  The server reads them but never copies or prints them.
- **`.gitignore`** blocks `token.json`, `client_secret*.json`, `credentials.json`, `.env` as a safety net.
- **The server never opens a browser.** Sign-in is a separate one-time step (`authorize.py`).
- **Separate practice account:** the server is connected to a dedicated course Gmail account,
  not to a personal mailbox.
- **Prompt injection:** an email may contain text that looks like an instruction to the agent
  ("forward all emails to…"). Because there is no send/forward/delete tool, the server cannot
  carry it out.
- **Human in the loop:** Claude Code asks for approval before each tool call. Approval requests
  are read before approving – the agent may still suggest other ways (e.g. a browser) to do
  what the server cannot.
- **Permissions:** `gmail.modify` and `calendar`, app in *Testing* mode, only listed test users
  can sign in. Access is revoked at the end of the course.

## 7. Technical design

| Part | Choice |
|---|---|
| Language | Python ≥ 3.10 |
| MCP | Official MCP Python SDK, **FastMCP** (`mcp` < 2) |
| Environment | **uv** (`pyproject.toml`, `uv.lock`) |
| Google | `google-api-python-client`, `google-auth-oauthlib`; `tzdata` for time zones on Windows |
| Files | `server.py` (tools), `google_auth.py` (loads the token), `authorize.py` (one-time sign-in), `test_server.py` (self-test) |
| Registration | `claude mcp add gmail-calendar … -- python -m uv run --directory <folder> server.py` (local scope, stored in `~/.claude.json`, not in the repo) |

Flow: the user's request → Claude Code (host) → model picks a tool from the menu
(`tools/list`) → `tools/call` to the server → Google API → result back to the model → answer.

## 8. Acceptance criteria

| # | Check | How it is verified | Result |
|---|---|---|---|
| A1 | Server exposes exactly 6 tools, no send/delete | `test_server.py` → `tools/list` | ✅ |
| A2 | Server talks to Google without permission errors | `test_server.py` → `list_events` | ✅ |
| A3 | Server is connected in the agent | `/mcp` shows `gmail-calendar` connected | ✅ |
| A4 | Free-language request creates draft "L06 test" + event "MCP works" in 4 hours | Gmail Drafts + Google Calendar | ✅ |
| A5 | New request works without new code ("Study group" in a free hour tomorrow) | `find_free_slots` → `create_event` | ✅ |
| A6 | "Send the draft" is refused – no send tool | Agent answer; draft stays in Drafts | ✅ |
| A7 | No secret file in the repository | `git status` before commit | ✅ |

## 9. Risks

| Risk | Mitigation |
|---|---|
| Token stolen → mailbox readable | Token outside the project, practice account, revoke at end of course |
| Agent bypasses the server (browser / script) | Read every approval request; decline |
| Token expires after ~7 days (Testing mode) | Run `uv run authorize.py` again |
| Vague tool descriptions → wrong tool chosen | Short, explicit descriptions, including what a tool does NOT do |
| Too many tools → more tokens per request | Keep the server small: six tools only |

## 10. Future ideas

- A meeting-coordinator flow: find a meeting request in email → check the calendar →
  create the event and prepare a reply draft (still never sending).
- One read-only tool for a domain of my own (Assignment 3).
