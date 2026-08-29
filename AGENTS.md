# AGENTS.md

This file provides guidance to AI coding agents (OpenAI Codex, GitHub Copilot, etc.) when working with code in this repository.

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
- **`models.py`** — `Post` (stock research with ticker, prices, thesis), `Comment`, `Vote` (unique per user/post, used for portfolio inclusion)
- **`views.py`** — 20+ views handling CRUD, voting, likes, PDF generation, portfolio/regime analysis. Business logic lives directly in views.
- **`finance.py`** — Portfolio metrics: VaR (historic, Cornish-Fisher, CVaR), stock stats via yfinance
- **`regime.py`** — Market regime detection using Hurst exponent and portfolio optimization (cvxpy). Helper functions `annualized_return_from_percent()` and `annualized_std_from_percent()` handle empty-array edge cases (return `np.nan`); used by `return_regime_graph()`, `return_portfolio_regime_graph()`, and `analyse_regime()`. Uses `matplotlib.use('Agg')` at module top — **required** to prevent "Starting a Matplotlib GUI outside of the main thread" crash in Django worker threads. `pct_change(fill_method=None)` used throughout since data is pre-filled with `ffill()` before calling `pct_change()`.
- **`ta.py`** — `TABacktester` class for SMA crossover, RSI, and mean-reversion backtesting
- **`utils.py`** — `render_to_pdf()` helper using xhtml2pdf

### Data flow for portfolio views
`/portfolio` and `/summary` pull tickers from `Post` objects where `include=True`, fetch price data via yfinance, run regime analysis from `regime.py`, and render results. `/pdf/` endpoints generate downloadable reports using `utils.render_to_pdf()`.

### Database
SQLite3 in development; PostgreSQL in production via `DATABASE_URL` env var. 12 migrations under `blog/migrations/`.

### Deployment
Heroku via `Procfile` (`gunicorn config.wsgi`). Static files served by WhiteNoise. Environment variables (`SECRET_KEY`, `DATABASE_URL`, `ANTHROPIC_API_KEY`) loaded from `.env` via `environs`.

#### WhiteNoise configuration (Django 4.2+)
`whitenoise.middleware.WhiteNoiseMiddleware` must be placed **immediately after** `SecurityMiddleware` in `MIDDLEWARE`. Do **not** add `whitenoise.runserver_nostatic` to `INSTALLED_APPS`. Static file storage uses the `STORAGES` dict (not the deprecated `STATICFILES_STORAGE` string):
- `DEBUG=True` → `StaticFilesStorage` (no compression, avoids manifest errors in dev)
- `DEBUG=False` → `CompressedManifestStaticFilesStorage`

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

To swap to Redis in production, change `CACHES["default"]["BACKEND"]` to `"django.core.cache.backends.redis.RedisCache"` and set `"LOCATION"` to the `REDIS_URL` env var.

## Key Dependencies
- **yfinance / pandas-datareader** — market data fetching
- **cvxpy** — portfolio optimization in `regime.py`
- **hurst** — Hurst exponent calculation for regime detection
- **xhtml2pdf / reportlab** — PDF report generation
- **django-crispy-forms + crispy-bootstrap4** — form rendering (`CRISPY_ALLOWED_TEMPLATE_PACKS` and `CRISPY_TEMPLATE_PACK` both set to `"bootstrap4"`)
