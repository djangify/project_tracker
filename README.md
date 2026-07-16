![page tracker header](https://github.com/djangify/project_tracker/blob/128cce0011da695400436adba5060c5f5c32e8c7/todiane-project tracker.png)

# Tracker

A self-hosted workspace for running multiple small businesses at once: a
cross-project dashboard, tasks scheduled by day (table / board / calendar
views), a lightweight CRM, and Notion-style note pages — all in one place,
for one person, on your own server.

Built with Django. No SaaS subscription, no third-party accounts, your data
stays in your own SQLite file.

## Features

- **Dashboard** — what's due today, this week's plan, a clash warning when
  two businesses land tasks on the same day, and a work log with weekly
  totals.
- **Tasks** — one task list, three views (table, board, calendar), filterable
  by project.
- **Work sessions** — log time against a task; it rolls up to the project
  and the week automatically.
- **CRM** — contacts with a pipeline status, follow-up reminders (with an
  email digest command), and an interaction log per contact.
- **Pages** — nestable, Notion-style notes with an Editor.js block editor,
  favorites, and soft-delete trash. Pages can link to a project or a contact.

See [`NOTION_UPGRADE_PLAN.md`](NOTION_UPGRADE_PLAN.md) if present in your
checkout for the full design rationale (it's not tracked in this public repo).

## Stack

- Django 5.2.9, Django REST Framework
- SQLite
- Tailwind CSS v4 (`@tailwindcss/cli`, no Node build framework)
- Gunicorn + WhiteNoise for production; Caddy (or any reverse proxy) in front
  for HTTPS

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

Visit `http://127.0.0.1:8000/`, log in with the superuser you created (auth
is via Django admin login), and you're in.

Rebuild Tailwind's CSS any time you add classes to a template:

```bash
node_modules/.bin/tailwindcss -i static/src/input.css -o static/css/output.css --minify
```

## Running tests

```bash
python manage.py test
```

## Deploying

This is built to run as a single process behind a reverse proxy:

```bash
DEBUG=False
python manage.py collectstatic --noinput
gunicorn config.wsgi:application --bind 127.0.0.1:8002 --workers 2 --timeout 60
```

Set `ALLOWED_HOSTS` and (if needed) `CSRF_TRUSTED_ORIGINS` in `.env` to your
real domain, and put HTTPS termination (Caddy, nginx, etc.) in front of
gunicorn.

## Scope

Single user, one browser at a time. No multi-user accounts, no real-time
collaboration, no Notion import. See the design notes in the repo for the
full list of what's deliberately out of scope.

## License

MIT — see [`LICENSE`](LICENSE).
