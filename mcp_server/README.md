# Content Calendar MCP Server

This lets you manage your content calendar directly from **Claude Desktop**,
**Cowork**, or **Claude Code** — list this week's content, create items, move
dates, change status, and generate drafts — without opening the app's UI.

It's the same tools the in-app Assistant uses, exposed over MCP's **stdio**
transport. Because it's a single-user local install, there's nothing to host and
no auth token to manage: Claude launches the server as a subprocess on demand.

## Requirements

- **The Claude Desktop app, installed and signed in.** This connector works with
  Claude Desktop (it launches the server on your own machine). It does **not**
  work from claude.ai in a web browser or on a phone — that would need a
  publicly-hosted HTTPS version. Any Claude plan that supports MCP/custom
  connectors will do.
- This project installed and working (its virtualenv, its SQLite database).
- The Python dependencies installed (`pip install -r requirements.txt`), which
  now include `mcp`.

## Does this cost money? (API key vs. your Claude subscription)

Managing your calendar through Claude Desktop runs on **your Claude
subscription — no API key, no per-token cost.** The tools that list, create,
move, edit and schedule content are just database operations.

- **Free (no API key):** everything driven from Claude Desktop, *including
  writing new content* — you ask Claude to write the captions and it saves them
  with `create_content_item`. Claude does the writing on your subscription.
- **Uses your API key (costs extra):** only the two buttons *inside the app* —
  the **✨ Generate** panel and the **Assistant** chat page — plus the
  `generate_draft` / `distill_voice` MCP tools, which call the provider directly.
  Set a key up in **AI Settings** only if you want those. You can ignore them
  entirely and let Claude Desktop do the writing for free.

## Run it manually (to check it starts)

```bash
python manage.py runmcp
```

It will print `Starting content-calendar MCP server (stdio)…` to stderr and then
wait for a client on stdin/stdout. Press Ctrl-C to stop. You normally don't run
it yourself — Claude starts it for you using the config below.

## Connect it to Claude

Add one entry pointing at **this install**. Use the full path to the project's
Python (the virtualenv) and set `cwd` to the project root.

### Claude Desktop / Cowork

Edit `claude_desktop_config.json` (Settings → Developer → Edit Config) and add:

```json
{
  "mcpServers": {
    "content-calendar": {
      "command": "C:\\Users\\you\\path\\to\\tracker\\trackervenv\\Scripts\\python.exe",
      "args": ["manage.py", "runmcp"],
      "cwd": "C:\\Users\\you\\path\\to\\tracker"
    }
  }
}
```

On macOS/Linux the `command` is `.../venv/bin/python` and paths use `/`.
Restart Claude Desktop; "content-calendar" appears in the tools menu.

### Claude Code

From the project directory:

```bash
claude mcp add content-calendar -- ./trackervenv/Scripts/python.exe manage.py runmcp
```

(Windows PowerShell: use the full path to `python.exe`.)

## Tools

| Tool | What it does | Example prompt |
|---|---|---|
| `list_content_items` | List items, optionally by date range / status | "What content do I have scheduled this week?" |
| `get_calendar_month` | List everything scheduled in a month | "Show me everything planned for August 2026." |
| `create_content_item` | Add a content item | "Add a Reel for Aug 12 titled 'Morning routine'." |
| `update_status` | Set pipeline status or approval status | "Approve item 5." / "Mark item 5 as published." |
| `reschedule_content_item` | Move an item to another date | "Move item 3 to next Friday." |
| `generate_draft` | Draft an item from a brief and/or template | "Draft an Instagram post about summer skincare for Aug 20." |
| `distill_voice` | Update the reusable voice profile from samples | "Here are three of my posts — learn my voice: …" |

Dates are `YYYY-MM-DD`. `generate_draft` and `distill_voice` use whichever AI
provider is active in AI Settings.
