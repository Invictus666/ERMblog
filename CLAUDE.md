# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ERMTool (Equity Research Management Tool) — a Django web app for managing stock research, portfolio analysis, and trading strategy backtesting. Users create research posts per ticker, vote on portfolio inclusion, and run regime/technical analysis.

## Common Commands

```bash
# Activate virtual environment (Windows)
.\venv\Scripts\activate

# Development server
python manage.py runserver

# Database migrations
python manage.py makemigrations
python manage.py migrate

# Run tests
python manage.py test

# Collect static files (production)
python manage.py collectstatic

# Deploy to Heroku
./deploy.bat
```

## Architecture

### Apps
- **`config/`** — Django project settings, root URL config, WSGI/ASGI entry points
- **`accounts/`** — User registration only (`SignUpView`); authentication handled by Django's built-in auth
- **`blog/`** — All core functionality: research posts, comments, votes, portfolio analysis

### Core `blog/` modules
- **`models.py`** — `Post` (stock research: `title` is `CharField(max_length=50)`; `business`/`pros`/`cons`/`rationale` are `TextField(max_length=500)` — these lengths match a migration already applied against the live database, so don't widen them without a new migration), `Comment`, `Vote` (unique per user/post, used for portfolio inclusion)
- **`views.py`** — 20+ views handling CRUD, voting, likes, PDF generation, portfolio/regime analysis. Business logic lives directly in views.
- **`finance.py`** — Portfolio metrics: VaR (historic, Cornish-Fisher, CVaR), stock stats via yfinance. `Maximum Drawdown Date` is formatted with `.strftime('%Y-%m-%d')` (date only, no time-of-day) in both `get_stock_stats()` and `get_portfolio_stats()`.
- **`regime.py`** — Market regime detection using Hurst exponent and portfolio optimization (cvxpy). Helper functions `annualized_return_from_percent()` and `annualized_std_from_percent()` handle empty-array edge cases (return `np.nan`); used by `return_regime_graph()`, `return_portfolio_regime_graph()`, and `analyse_regime()`. Uses `matplotlib.use('Agg')` at module top — **required** to prevent "Starting a Matplotlib GUI outside of the main thread" crash in Django worker threads; do not remove it. `plot_regime_color_new()` must return `(fig, dataset)` — an actual `matplotlib.figure.Figure` — not the `pyplot` module itself: `views.py`'s `return_regime()` calls `fig.tight_layout()`, `fig.savefig(...)`, and `plt.close(fig)` on the returned object, and `plt.close()` raises `TypeError` if handed the module instead of a `Figure`. (This exact regression broke chart rendering in production once already — see git history around commit `8ba18758`.) `pct_change(fill_method=None)` used throughout since data is pre-filled with `ffill()` before calling `pct_change()`.
- **`ta.py`** — `TABacktester` class for SMA crossover, RSI, and mean-reversion backtesting
- **`utils.py`** — `render_to_pdf()` helper using xhtml2pdf

### Data flow for portfolio views
`/portfolio` and `/summary` pull tickers from `Post` objects where `include=True`, fetch price data via yfinance, run regime analysis from `regime.py`, and render results. `/pdf/` endpoints generate downloadable reports using `utils.render_to_pdf()`.

### Database
SQLite3 in development; PostgreSQL in production via `DATABASE_URL` env var. 12 migrations under `blog/migrations/`.

### Deployment
**Live production site**: https://ngwaichung1974.pythonanywhere.com/, served from `/home/NgWaiChung1974/ERMTool` on PythonAnywhere (username `NgWaiChung1974`), using a Linux virtualenv at `~/venv` — **not** `<project>/venv` (that path, and `~/mysite`, contain leftover Windows-style venvs with no `bin/activate` and are unused; don't target them).

**GitHub repo**: `origin` → `https://github.com/Invictus666/ERMblog.git` (not the older `Modeus1974/ERMTool`, which is now stale/unused). Pushing to `main` auto-deploys via `.github/workflows/deploy.yml`, which SSHes into PythonAnywhere (deploy key stored as the `PA_SSH_PRIVATE_KEY` repo secret) and runs: `git fetch && git reset --hard origin/main` → reinstall `requirements.txt` → `migrate` → `collectstatic --noinput` → `touch` the WSGI file to reload.

**Important**: because deploy does `git reset --hard`, any edit made directly on the server outside of git (via a PythonAnywhere console, etc.) will be silently discarded on the next push. Always make changes locally and push — never hand-edit files on the server. (This already happened once: an uncommitted, half-finished server-side edit to `regime.py` was mistakenly treated as canonical and had to be reverted — see commit `8ba18758`.)

Heroku (`Procfile`, `gunicorn config.wsgi`) is a legacy/secondary deploy target, not the one actively serving traffic. Environment variables (`SECRET_KEY`, `DATABASE_URL`, `ANTHROPIC_API_KEY`) loaded from `.env` via `environs`.

#### WhiteNoise configuration (Django 4.2+)
`whitenoise.middleware.WhiteNoiseMiddleware` must be placed **immediately after** `SecurityMiddleware` in `MIDDLEWARE`. Do **not** add `whitenoise.runserver_nostatic` to `INSTALLED_APPS`. Static file storage uses the `STORAGES` dict (not the deprecated `STATICFILES_STORAGE` string):
- `DEBUG=True` → `StaticFilesStorage` (no compression, avoids manifest errors in dev)
- `DEBUG=False` → `CompressedManifestStaticFilesStorage`

**Note**: `DEBUG` is currently hardcoded to `True` in `config/settings.py` (not read from env), including on the live server — so static files are always served unhashed via `StaticFilesStorage`/PythonAnywhere's static mapping, with no far-future cache headers. This is a known issue, not by design; flag it if asked to touch settings.

`blog/static/css/base.css` is the source stylesheet; `staticfiles/css/base.css` is a `collectstatic`-generated copy that is (unusually) also checked into git. When editing `base.css` by hand outside of running `collectstatic`, update both copies so they don't drift.

#### Database
`DATABASE_URL` env var is always required (no SQLite fallback in current config). PythonAnywhere is also an active deployment target (`.pythonanywhere.com` in `ALLOWED_HOSTS`).

### Caching

Yahoo Finance calls are expensive (network + compute). All data-fetch functions cache their results using Django's file-based cache (`cache/` dir at project root, TTL in parentheses):

| Function | File | TTL |
|---|---|---|
| `get_current_price(ticker)` | `finance.py` | 5 min |
| `get_stock_stats(stock, years)` | `finance.py` | 1 hr |
| `get_portfolio_stats(portfolio, years)` | `finance.py` | 1 hr |
| `build_stock_prices_dataframe(...)` | `regime.py` | 1 hr |
| `build_portfolio_prices_dataframe(...)` | `regime.py` | 1 hr |
| `generate_business_summary` (full API response) | `views.py` | 24 hr |

Cache keys use `|`-joined sorted tickers so argument order doesn't affect hits. To force a refresh, hit `GET /api/clear-cache` (login required) or delete the `cache/` directory.

**The deploy workflow does not clear this cache.** After deploying a code change that alters a *computed value* (not just presentation), cached entries for already-viewed tickers can keep serving the old shape for up to their TTL. Clear `cache/` on the server (or hit `/api/clear-cache`) after such a change if you need it to show immediately rather than within the hour.

To swap to Redis in production, change `CACHES["default"]["BACKEND"]` to `"django.core.cache.backends.redis.RedisCache"` and set `"LOCATION"` to the `REDIS_URL` env var.

## Key Dependencies
- **yfinance / pandas-datareader** — market data fetching
- **cvxpy** — portfolio optimization in `regime.py`
- **hurst** — Hurst exponent calculation for regime detection
- **xhtml2pdf / reportlab** — PDF report generation
- **django-crispy-forms + crispy-bootstrap4** — form rendering (`CRISPY_ALLOWED_TEMPLATE_PACKS` and `CRISPY_TEMPLATE_PACK` both set to `"bootstrap4"`)
