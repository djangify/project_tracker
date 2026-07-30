![Project Tracker](todiane-project-tracker-image.png)
# Tracker

A self-hosted workspace for running multiple small businesses at once — and now
a full content operation on top: a cross-project dashboard, tasks, a lightweight
CRM, Notion-style notes, digital products, email sequences, and a **content
calendar with a built-in AI engine** you can drive from the app *or* straight
from Claude Desktop.

Built with Django. No SaaS subscription, no third-party accounts, your data
stays in your own SQLite file. Runs as a normal web app or as a packaged
desktop app (`.exe`).

---

## Features

### Business management

- **Dashboard** — what's due today, this week's plan, a clash warning when two
  businesses land tasks on the same day, and a work log with weekly totals.
- **Projects** — track several businesses/projects side by side, each with its
  own status, priority, and "last worked on" timestamp.
- **Tasks** — one task list, three views (**table**, **board**, **calendar**),
  filterable by project, with recurring "habit" tasks tracked per day/week/month.
- **Work sessions** — log time against a task; it rolls up to the project and
  the week automatically.
- **CRM** — contacts with a pipeline status, follow-up reminders (with an email
  digest command), and an interaction log per contact.
- **Pages** — nestable, Notion-style notes with a block editor, favorites, and
  soft-delete trash. Pages can link to a project or a contact.
- **Products** — digital products tied to a business, with an optional
  deliverable file, a sales log, and simple funnel steps.
- **Email sequences** — drip sequences of steps with per-step delays and
  enrollments.
- **Assets** — a library of source material (upload a file or paste text /
  transcripts), with prompt templates, a voice profile, and generation jobs for
  turning that material into content.

### Content calendar

- **Content items** — everything from a content-planning spreadsheet in one
  record: scheduled date, pillar, content type, topic, platforms, hook, caption,
  call to action, hashtags, tags/links, audio, a cover image/video, the
  published link, plus a production **status** and an **approval status**.
- **Three views** — a Sun–Sat **calendar** grid, a **board** grouped by approval
  status (review and approve here), and a filterable **table**.
- **Platforms** — TikTok, Instagram, Pinterest, Facebook, YouTube and WhatsApp
  seeded out of the box; add more without a code change.

### AI engine (bring your own provider)

- **AI provider settings** — pick **OpenAI**, **Anthropic (Claude)** or **Google
  Gemini** and swap between them without touching code. Your API key is
  **encrypted at rest** (Fernet, derived from `SECRET_KEY`), never stored in
  plain text. A "test connection" button confirms it works.
- **Voice profile** — paste a few samples of your own writing and the app
  distils a reusable voice so generated content sounds like you.
- **Content templates** — named recipes (e.g. "Instagram carousel") that produce
  a content item's fields (hook → caption → CTA → hashtags) in one ordered run.
- **Generate panel** — pick a template or write a brief, choose a date, and get a
  draft content item dropped into the calendar as "Ready for Approval."
- **Assistant** — a chat page that *acts*: ask it to list, create, move, approve,
  schedule, or draft content and it uses the tools to do it.

### Use it from Claude Desktop (MCP)

The content tools are also exposed as an **MCP server**, so you can manage your
calendar directly from **Claude Desktop** — list this week's content, create
items, move dates, change status, or have Claude write and save drafts.

- **Auto-connect** — on first launch the app registers itself with Claude Desktop
  automatically (no config file editing). You just restart Claude Desktop once.
- **No API key needed for this path** — Claude Desktop does the thinking on your
  **Claude subscription**. The API key above is only for the in-app Generate
  panel and Assistant chat.
- See [`mcp_server/README.md`](mcp_server/README.md) for the tool list, example
  prompts, and manual setup.

---

## Stack

- Django 5.2, Django REST Framework
- SQLite (single file)
- Tailwind CSS v4 (`@tailwindcss/cli`, no Node build framework) + a little
  vanilla JS/`fetch` — no front-end framework
- AI SDKs: `openai`, `anthropic`, `google-genai`; keys encrypted with
  `cryptography` (Fernet)
- `mcp` (Model Context Protocol) for the Claude Desktop server
- Gunicorn + WhiteNoise for server deployments; PyWebView + Waitress +
  PyInstaller for the packaged desktop `.exe`

---

## Getting started (local development)

```bash
git clone https://github.com/djangify/project_tracker.git
cd project_tracker

python -m venv trackervenv
source trackervenv/bin/activate   # Windows: trackervenv\Scripts\activate
pip install -r requirements.txt

npm install

cp .env.example .env
# Edit .env — at minimum set SECRET_KEY. Leave DEBUG=True for local dev.

python manage.py migrate
python manage.py createsuperuser

# Build Tailwind's output.css from the source file
node_modules/.bin/tailwindcss -i static/src/input.css -o static/css/output.css --minify

python manage.py runserver
```

Visit `http://127.0.0.1:8000/`, log in with the superuser you created (auth is
via Django admin login), and you're in.

Rebuild Tailwind's CSS any time you add classes to a template:

```bash
node_modules/.bin/tailwindcss -i static/src/input.css -o static/css/output.css --minify
```

### Turning on the AI features (optional)

The app works fully without AI. To enable generation:

1. Open **AI Settings** in the app.
2. Paste an API key for OpenAI, Anthropic, or Gemini, pick which is active, and
   hit **Test connection**.

That powers the in-app **✨ Generate** panel and the **Assistant** chat. To drive
the calendar for free from Claude Desktop instead, see the MCP section above —
that uses your Claude subscription rather than an API key.

---

## Running tests

```bash
python manage.py test
```

## Run the MCP server manually

```bash
python manage.py runmcp        # stdio; for Claude Desktop / Code
python manage.py connect_claude  # register this install with Claude Desktop
```

## Building the desktop app

```bash
pyinstaller project_tracker.spec
```

Produces `dist/ProjectTracker/` containing `ProjectTracker.exe` (the app window)
and `ProjectTracker-mcp.exe` (the MCP server Claude Desktop launches). Ship the
whole folder.

## Deploying (server)

Runs as a single process behind a reverse proxy:

```bash
DEBUG=False
python manage.py collectstatic --noinput
gunicorn config.wsgi:application --bind 127.0.0.1:8002 --workers 2 --timeout 60
```

Set `ALLOWED_HOSTS` and (if needed) `CSRF_TRUSTED_ORIGINS` in `.env` to your real
domain, and put HTTPS termination (Caddy, nginx, etc.) in front of gunicorn.

---

## Scope

Single user, one browser at a time. No multi-user accounts, no billing, no
real-time collaboration. The MCP/Claude Desktop connection is local (stdio) — it
works from the Claude Desktop app on the same machine, not from claude.ai in a
browser.

## License

MIT — see [`LICENSE`](LICENSE).
