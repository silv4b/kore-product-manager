# AGENTS.md — Kore Product Manager

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.14, Django 6.0 |
| Package manager | **uv** (not pip, not pipenv) |
| Database | PostgreSQL 14 via Docker (port 5437), **SQLite fallback** if `DB_NAME`/`DB_USER`/`DB_PASSWORD` env vars are empty |
| Frontend | Tailwind CSS v4 + Basecoat UI, HTMX, Lucide icons |
| Auth | django-allauth (email/username login), DRF + SimpleJWT for API |
| API | Django REST Framework + drf-spectacular (OpenAPI) |
| Linter | **ruff** (line-length=120, excludes migrations, rules: DJ/E/F/W/I/UP/B) |
| Test | pytest + pytest-cov + factory-boy |
| Task runner | poethepoet (`uv run poe <task>`) |
| Infra | Docker, gunicorn, whitenoise (staticfiles), signed_cookies session engine |

## Project structure

```
kore-product-manager/
├── api/                  # DRF app (views, serializers, tests)
├── partners/             # Partners app (customers + suppliers CRUD)
│   └── templatetags/     # partner_masks.py (CPF/CNPJ/phone masks)
├── products/             # Main app (products, categories, movements, price history)
│   ├── management/commands/
│   ├── migrations/
│   └── tests/            # factories.py, mixins.py, test_*.py
├── kore-product-manager/ # Django project settings/urls/wsgi
├── static/               # CSS, JS, images
│   ├── css/input.css     # Tailwind source (imports basecoat)
│   └── css/output.css    # Compiled (npm run build)
├── templates/            # Django templates by app
│   ├── partners/
│   └── products/
├── docs/                 # plano-de-acao.md, manual-docker.md
├── AGENTS.md
├── pyproject.toml        # Python deps + ruff config + poe tasks
├── package.json          # npm deps (tailwind, basecoat)
└── docker-compose.yaml   # postgres + app services
```

## Key commands

```bash
# Run dev server (port 8005)
uv run python manage.py runserver 8005

# CSS build (required after Tailwind class changes)
npm run build

# Run tests with SQLite (avoid postgres timeouts)
DB_NAME="" DB_USER="" DB_PASSWORD="" uv run pytest --tb=short

# Run tests with coverage
DB_NAME="" DB_USER="" DB_PASSWORD="" uv run pytest

# Lint
.venv/Scripts/ruff.exe check .

# Auto-fix lint
.venv/Scripts/ruff.exe check . --fix

# Migrations
uv run python manage.py makemigrations
uv run python manage.py migrate

# Create superuser
uv run python manage.py createsuperuser

# Poe shortcuts
uv run poe pytest
uv run poe coverage
uv run poe npm_build
```

**Important:** `.venv/Scripts/` prefix is required on Windows (msys2). The `.venv` has lock issues with `.pyd` files on Windows — retry `uv sync` if it fails.

## Coding conventions

### Python

- **Line length:** 120 (enforced by ruff)
- **Imports:** isort-style (ruff I rule). Group: stdlib → django → third-party → local. One blank line between groups.
- **Strings:** Double quotes (`"`) everywhere (ruff UP will flag single quotes)
- **Django models:** `Meta` class **before** `__str__` (ruff DJ012)
- **Django views:** `@login_required` on all auth-required views. Check `request.headers.get("HX-Request")` for HTMX.
- **HTMX endpoints:** Return `HttpResponse(status=204)` when called via HTMX background sync (no content swap needed).
- **Avoid `assert`** in production code — use `if x is None: raise ValidationError(...)` instead.
- **Timezone-aware dates:** Always use `timezone.make_aware()` when parsing user-provided dates (Django `USE_TZ=True`).
- **DB aggregations:** Use `ExpressionWrapper` + `Sum`/`Count` at the DB level, never `sum(p.field for p in queryset)` in Python.

### JavaScript (static/js/)

- Theme toggle: `toggleTheme()` toggles `.dark` + `hx-post` background sync to server
- View mode: `setViewMode(context, mode)` toggles UI instantly + `hx-get` background sync
- CSRF token: `meta[name="csrf-token"]` + `htmx:configRequest` handler
- Brazilian masks available via `Masks.cpf()`, `Masks.cnpj()`, `Masks.phone()`, `Masks.email()`

### Templates

- Base template: `templates/base.html` (extends pattern)
- HTMX fragment swapping: use `hx-swap="none"` for background-only requests
- View mode buttons: `data-view-mode="true" data-mode="grid|table"`

## Three-tier boundaries

### Always do

- Run `ruff check .` before committing
- Run tests before committing
- Use `DB_NAME="" DB_USER="" DB_PASSWORD=""` to force SQLite for tests (Postgres test DB `test_kore_db` causes conflicts)
- Add type hints to new function signatures

### Ask first

- Architecture changes (new apps, new dependencies)
- Changing auth flows or session handling
- Modifying database schema or migrations
- Adding production secrets or env vars

### Never do

- Commit `.env`, `.env.docker`, or any file with real secrets
- Remove `null=True, blank=True` from model fields without discussion
- Use `ALLOWED_HOSTS = ["*"]` — read from env var instead
- Hardcode `SECRET_KEY` — use `os.getenv("SECRET_KEY", fallback)`
- Use `dotenv` package (unmaintained) — use `python-dotenv` instead (import as `from dotenv import load_dotenv`)

## Commit protocol

Before staging any changes, read `docs/batched-commits.md` and follow the
4-step protocol: analyze → group → present → execute only on user approval.
Never push — the user does that manually.
