# Contributing

Thanks for taking a look at this project. It's a single-user tool built for
a specific workflow (running a couple of small businesses solo), so the
scope is intentionally narrow — see the "Scope" section in the
[README](README.md) for what's explicitly out of bounds (multi-user,
real-time collaboration, third-party import tooling, etc.). PRs in that direction are
likely to be declined, so it's worth opening an issue to discuss first if
you're planning something bigger than a small fix.

## Reporting bugs

Open an issue with:
- What you did, what you expected, what happened instead
- Django/Python version, and whether you're running locally or deployed
- Any traceback from the terminal or browser console

## Suggesting features

Open an issue describing the problem you're trying to solve, not just the
feature — it's easier to evaluate against the project's scope that way.

## Pull requests

1. Fork the repo and create a branch off `main`.
2. Keep the change focused — one fix or feature per PR.
3. Add or update tests for any behavior change (`python manage.py test`
   should stay green).
4. If you touched templates, rebuild Tailwind's CSS before committing:
   ```bash
   node_modules/.bin/tailwindcss -i static/src/input.css -o static/css/output.css --minify
   ```
5. Run `python manage.py makemigrations --check` to make sure no migration
   is missing.
6. Open the PR against `main` with a short description of what changed and
   why.

## Development setup

See "Getting started" in the [README](README.md).
