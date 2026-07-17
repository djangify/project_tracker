# Release package — what's in here

This folder is a staging area for the zip you sell/distribute. It is **not**
part of the running app — nothing here is imported by Django. Move or delete
it any time without affecting Tracker itself.

## Before you zip, in order

1. **Rebuild the .exe.** The PyInstaller spec (`project_tracker.spec`, at the
   project root) was just updated to include the three new apps — `assets`,
   `products`, `sequences`. The existing `dist/ProjectTracker/` folder
   predates that change and does **not** have the new features in it. From
   the project root, with `trackervenv` active:

   ```
   pyinstaller project_tracker.spec
   ```

   Also check `project_tracker.spec` — `console=True` is currently set for
   debugging a startup crash (per the comment in the spec file). Confirm
   that's resolved and flip it to `console=False` before shipping, or buyers
   will see a terminal window behind the app.

2. **Copy the rebuilt app** from `dist/ProjectTracker/` into
   `release-package/ProjectTracker/` (replacing the placeholder file
   already there).

3. **Test the exe** exactly the way a buyer would: unzip on a clean-ish
   machine (or at least a fresh folder), double-click, log in with the
   default `admin@example.com` / `admin123`, confirm the example content
   (prompt templates, sample assets, the example generated page) shows up
   under Assets and Pages automatically.

4. **Fill in the placeholders** — search this folder for `[ ]` and
   `TODO` and replace: your support email, your pricing/license terms in
   `LICENSE.txt`, and the "where to buy updates" line in the quickstart.

5. **Zip the whole `release-package` folder's contents** (not the folder
   itself — buyers should unzip and land directly on `ProjectTracker/`,
   `instructions/`, etc., not one extra layer of nesting).

## What's in here

- `ProjectTracker/` — the packaged .exe goes here (placeholder for now).
- `instructions/` — everything a buyer needs to get running and find their
  way around, written in plain language, no jargon.
- `skills/` — an optional file for buyers who use Claude/Claude Code/Cowork
  themselves. It's not required to use Tracker — it just speeds up initial
  setup (writing their first prompt templates, describing their brand
  voice) for anyone who wants an AI assistant to help configure it.
- `LICENSE.txt` — single-user license terms. **Draft only — this is not
  legal advice.** Have someone review it (or adapt a template from a
  service like TermsFeed / an actual solicitor) before relying on it.

## AI key setup

Buyers add their own Anthropic API key inside the app itself — **⚙️
Settings** in the sidebar — the same way Djangify handles it. It's stored
in their local database, not an environment variable, so it works
identically in the packaged .exe and in dev, with no config files to edit.
Steps are in `instructions/SETTING-UP-AI-FEATURES.md`.

Note: the key is stored as plain text in the local SQLite database (not
encrypted at rest). Since the whole app is single-user and local-only,
that's the same trust boundary as everything else it stores — but worth
knowing if you ever want to harden it further.
