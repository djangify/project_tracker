# Tracker → Notion-Style Workspace: Build Spec

A phased plan to turn Tracker into a personal Notion-style workspace with a unified
dashboard. Written to be executed phase by phase by Claude Code (Sonnet is fine).
Complete and verify each phase before starting the next.

## Current codebase (do not assume — this is verified)

- Django 6.0, DRF, db.sqlite3, whitenoise, gunicorn (deployed directly via gunicorn in
  `start_tracker.sh`; no Docker)
- Tailwind CSS v4 via `@tailwindcss/cli` (npm), output at `static/css/output.css`
- No rich-text editor is currently installed; Phase 1 introduces its own (Editor.js).
  If a page/block editor is needed elsewhere, add one explicitly.
- Single user, auth via Django admin login (`/accounts/login/` redirects to admin login)
- Apps:
  - `projects`: `Project` (name, status: active/paused/completed, priority, last_worked_on),
    `Task` (FK project, title, is_completed, order), `WorkSession` (FK project, start/end, notes, duration_minutes())
  - `crm`: `Contact` (platform, status pipeline, tags, follow_up_date, follow_up_1/2/3_done,
    revenue, follow_up_overdue property), `FollowUpTemplate`, `Interaction` (FK contact, channel, date, notes)
  - `core`: `SiteConfiguration`, `TimeStampedModel`, home view, context processor `site_config`
- Templates: `templates/base.html` (indigo navbar, Tailwind), app templates in each app
- URLs: `/` → core, `/projects/`, `/crm/`, `/admin/`

## Conventions for all phases

- All new views require login (`LoginRequiredMixin` / `@login_required`)
- Use Tailwind v4 utility classes consistent with existing templates; rebuild CSS with
  the existing npm Tailwind CLI script after adding new template files
- Extend `templates/base.html`; don't create a second base template
- Register every new model in Django admin
- Write at least basic tests per phase (model + view smoke tests)
- Migrations: one per logical change, run `python manage.py makemigrations && migrate`

---

## Phase 1 — `pages` app: nested pages with a block editor

The Notion core: pages that nest infinitely, edited as blocks.

### Models (`pages/models.py`)

```python
class Page(models.Model):
    title = models.CharField(max_length=255, default="Untitled")
    icon = models.CharField(max_length=8, blank=True)  # single emoji
    parent = models.ForeignKey("self", null=True, blank=True,
                               on_delete=models.CASCADE, related_name="children")
    content = models.JSONField(default=dict, blank=True)  # Editor.js output
    # optional links into existing apps (Phase 3 uses these)
    project = models.ForeignKey("projects.Project", null=True, blank=True,
                                on_delete=models.SET_NULL, related_name="pages")
    contact = models.ForeignKey("crm.Contact", null=True, blank=True,
                                on_delete=models.SET_NULL, related_name="pages")
    is_favorite = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)  # trash, not hard delete
    position = models.PositiveIntegerField(default=0)  # sibling ordering
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["position", "created_at"]
```

Design decision: store page content as one JSONField holding Editor.js output rather
than a Block-per-row model. For a single user this is dramatically simpler (no ordering
tables, no N+1), and Editor.js handles block ordering/types client-side. Only move to a
Block model later if per-block backlinks are ever needed.

### Editor

Use **Editor.js** (https://editorjs.io) loaded from CDN (jsdelivr) in the page-edit
template. Plugins: header, list, checklist, quote, code, delimiter, table, inline-code,
marker. Do NOT use django-prose-editor for pages (keep it where it's already used).
- Editor.js `onChange` → debounce 1.5s → POST JSON to an autosave endpoint
- Autosave endpoint: DRF or plain JSON view `PATCH /pages/<id>/content/` saving
  `content` and `title`; return 200 + `updated_at`. CSRF token from cookie.
- Show a subtle "Saved"/"Saving…" indicator

### Views & URLs (`/pages/`)

- Page detail/edit (one view — it's single-user, always editable): title input (h1-styled,
  borderless), icon picker (plain emoji text input is fine), Editor.js holder, breadcrumbs
  from ancestors, list of child pages at the bottom, "+ New subpage" button
- Create (`POST /pages/new/`, optional `?parent=<id>`) → redirect to the new page
- Archive/restore/delete views; archived pages listed under a "Trash" view
- Favorite toggle (small JSON POST)

### Sidebar

Add a collapsible left sidebar to `base.html` (visible when authenticated):
- Links: Dashboard, Projects, CRM, then FAVORITES (favorite pages), then PAGES —
  the page tree (roots + expandable children, small ▸ toggles; render the tree
  server-side with a recursive template include; a few lines of vanilla JS for expand/collapse,
  persist expanded state in `localStorage`)
- "+ New page" at the bottom of the PAGES section
- Keep the existing top navbar; the sidebar is the primary nav on desktop, hidden behind
  a hamburger on mobile

### Verify Phase 1

Create nested pages 3 levels deep, edit with slash commands, refresh and confirm content
persisted, favorite a page, archive and restore one. Run tests.

---

## Phase 2 — Unified dashboard at `/`

Replace the current core home view with a real overview dashboard (login required).
One `DashboardView` in `core` that aggregates across all apps.

### Panels (each a card in a responsive grid)

1. **Working on now** — active projects ordered by `last_worked_on` desc (top 5):
   name, priority badge, last worked on ("3 days ago"), open-task count. Link to project.
2. **To do** — incomplete tasks across ALL active projects (top 10), grouped by project,
   with inline checkbox that completes the task via small JSON POST (no page reload).
3. **This week in CRM** — interactions in the last 7 days: count + list (contact name,
   channel, date). Header: "You've spoken to N people this week."
4. **Follow-ups due** — contacts where `follow_up_overdue` is true or `follow_up_date`
   ≤ today+3 days, excluding completed pipelines. Red highlight for overdue.
5. **Time this week** — total WorkSession minutes for last 7 days, split by project
   (simple horizontal bars with Tailwind widths, no chart library).
6. **Recent pages** — 5 most recently updated non-archived pages, plus favorites row.
7. **Pipeline snapshot** — contact counts by status (new / contacted / replied /
   in_conversation / converted) as a compact stat row, plus total revenue.

### Implementation notes

- All queries in `get_context_data`, use `select_related`/`prefetch_related`, and
  annotate counts rather than looping in templates
- Week = last 7 days (rolling), computed with `timezone.localdate()`
- Each panel is a separate template include (`core/templates/core/dashboard/_*.html`)
  so panels can be reworked independently
- Task-complete and favorite-toggle endpoints return JSON; ~20 lines of vanilla JS total

### Verify Phase 2

Seed sample data (management command or admin), load `/`, confirm each panel shows
correct numbers against manual queries, tick a task inline and confirm it persists.

---

## Phase 3 — Glue: search, linking, quick capture

1. **Global search** (`/search/?q=`): one view searching Page titles + content text,
   Project names/descriptions, Task titles, Contact names/handles/notes, Interaction
   notes. Postgres `SearchVector` where easy, `icontains` is acceptable. Grouped results
   page + search box in the sidebar. (Skip fancy keyboard palette unless trivial.)
2. **Linked pages** — surface `page.project` / `page.contact`:
   - Project detail: "Notes" section listing linked pages + "New page for this project"
   - Contact detail: same pattern
   - Page edit: small dropdown to link/unlink a project or contact
3. **Quick capture** — "+ New" button in the navbar with dropdown: New page / New task
   (pick project) / New contact / Log interaction. Small modal forms posting to existing
   create endpoints. This is what makes it feel like one workspace instead of three apps.

### Verify Phase 3

Search finds a word buried inside page content; create a page from a project and see it
listed both in the project and the sidebar tree; quick-capture a task from the dashboard.

---

## Phase 4 (optional, later) — user-defined databases

Notion's table/board views over custom schemas. Only build if Phases 1–3 leave a real gap:

- Models: `Database` (name, icon) → `Property` (FK database, name, type: text/number/
  select/multiselect/date/checkbox/url, config JSON) → `Row` (FK database, values JSONField)
- Views: table (sortable/filterable) and board (grouped by a select property, drag between
  columns is a stretch goal)
- A `Database` can be embedded in a page as a link block
- Do NOT migrate projects/crm into this system — they work; leave them

---

## Explicitly out of scope

Real-time collaboration, multi-user permissions, page version history, offline sync,
comments, mobile apps, importing from Notion. Single user, one browser at a time.

## Suggested execution order in Claude Code

One session per phase. Start each session with: "Read NOTION_UPGRADE_PLAN.md and the
existing models/templates it references, then implement Phase N. Run makemigrations,
migrate, and the tests before finishing."
