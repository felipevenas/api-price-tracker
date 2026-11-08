<div align="center">

# Price Tracker API 🏷️

**Resilient e-commerce price monitoring API built with FastAPI, Clean Architecture, DDD, and SOLID — with Celery/Redis scheduling, PostgreSQL history, Mercado Livre integration, Selenium Grid scaffolding, and JWT authentication.**

[![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-%3E%3D0.110-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![Celery](https://img.shields.io/badge/Celery-%3E%3D5.3-3781B8?style=for-the-badge&logo=celery&logoColor=white)](https://docs.celeryq.dev/)
[![Selenium](https://img.shields.io/badge/Selenium-%3E%3D4.18-43B02A?style=for-the-badge&logo=selenium&logoColor=white)](https://www.selenium.dev/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docs.docker.com/compose/)
[![License](https://img.shields.io/badge/License-Proprietary-red?style=for-the-badge)](LICENSE)

<br />

<p align="center">
  <a href="#overview"><b>Overview</b></a> •
  <a href="#stack"><b>Stack</b></a> •
  <a href="#architecture"><b>Architecture</b></a> •
  <a href="#quick-start"><b>Quick Start</b></a> •
  <a href="#configuration"><b>Configuration</b></a> •
  <a href="#api-surface"><b>API</b></a> •
  <a href="#testing"><b>Testing</b></a> •
  <a href="#deployment"><b>Deployment</b></a> •
  <a href="#known-limitations-mvp-trade-offs"><b>Limitations</b></a> •
  <a href="#governance"><b>Governance</b></a>
</p>

</div>

---

> **Repository:** [felipevenas/api-price-tracker](https://github.com/felipevenas/api-price-tracker) ·
> **Related governance:** [CONTRIBUTING.md](CONTRIBUTING.md) · [SECURITY.md](SECURITY.md) · [CHANGELOG.md](CHANGELOG.md)
>
> No public production URL or frontend repository is documented for this project.

## Overview

**Price Tracker API** lets a user register product URLs, set a target price and a per-product check interval, and keep a historical record of observed prices. A background pipeline wakes up every minute, finds products whose individual interval has expired, dispatches one Celery task per product, obtains the current price, and writes the result back to PostgreSQL.

The service is designed around three concerns:

1. **The HTTP API never blocks on scraping.** Product creation returns immediately; price acquisition is queued. The Celery Beat scheduler is the safety net that keeps monitoring moving.
2. **Every provider lookup is recorded, including failures.** A successful check updates `product_monitored.current_price`; both success and provider failure append to `price_history` and `audit_log`.
3. **Providers are replaceable.** Mercado Livre is currently read through its official API. The Selenium Grid + `ScraperFactory` path exists for additional stores, but no concrete Selenium scraper is registered yet (see [Known Limitations](#known-limitations-mvp-trade-offs)).

This repository contains **only the backend**. There is no bundled web client.

### What this service owns

| Area | Responsibility |
|---|---|
| Identity | Registration, login, profile read/update, password hashing with bcrypt, HS256 JWT issuance |
| Product catalog | Per-user product CRUD, target price, check interval, active flag |
| Scheduling | Celery Beat orchestration every 60 seconds, per-product interval enforcement, active-job deduplication |
| Price acquisition | Mercado Livre official API (items and catalog products); Selenium Grid adapter for future providers |
| History | Current price, chronological `price_history` rows with success/failure status and error message |
| Audit | Product create/update/delete and price-check success/failure with contextual JSONB details |
| Job observability | `worker_job` row per dispatched task (`enqueued`, `processing`, `completed`, `failed`) |
| Operations | Docker Compose stack, Alembic migrations, structured logs with request/task correlation IDs, `run.py` DX script |

### Core capabilities

- **FastAPI** with async request handlers and an OpenAPI schema at `/api/v1/openapi.json`.
- **Async SQLAlchemy 2.0 + asyncpg** with `NullPool`, avoiding event-loop pool conflicts between FastAPI and Celery.
- **Alembic-owned schema** with two revisions: initial tables and `worker_job`.
- **Celery + Redis** for asynchronous execution; **Celery Beat** for periodic orchestration.
- **Mercado Livre official API** client with OAuth 2.0 client credentials, `/items/{id}` lookup, `/products/{id}` fallback, and lowest-offer fallback.
- **Selenium Grid** service in Compose plus a domain-keyed `ScraperFactory`; remote WebDriver with CDP `navigator.webdriver` patch when `SELENIUM_HUB_URL` is set.
- **JWT authentication** via OAuth2 password flow, bcrypt password hashes, and a reusable `get_current_user` dependency.
- **Consistent JSON envelope** for route responses, plus a global exception handler and validation-error handler.
- **Correlation IDs**: incoming `X-Correlation-ID` is reused, otherwise generated; it is returned in the response header and injected into logs alongside Celery task IDs.
- **Developer experience**: `run.py` creates a virtualenv when needed, starts Compose, waits for PostgreSQL, applies migrations, and streams logs.

## Stack

Versions below are the **declared minimums** in [`requirements.txt`](requirements.txt) and the **pinned image tags** in [`docker-compose.yml`](docker-compose.yml) and [`Dockerfile`](Dockerfile). They are not a claim about the exact versions installed in a running environment.

| Layer | Technology | Declared version / image | Role |
|---|---|---|---|
| Language | Python | `3.10` (`python:3.10-slim`) | Runtime |
| Web | FastAPI | `>=0.110.0` | HTTP API and OpenAPI |
| Server | Uvicorn | `>=0.28.0` | ASGI server |
| Validation | Pydantic v2 + pydantic-settings | `>=2.2.1` | Schemas and `.env` settings |
| Persistence | SQLAlchemy (asyncio) | `>=2.0.28` | ORM and async sessions |
| Driver | asyncpg | `>=0.29.0` | PostgreSQL async driver |
| Migrations | Alembic | `>=1.13.1` | Schema revisions |
| Database | PostgreSQL | `postgres:15-alpine` | Primary store |
| Queue | Celery | `>=5.3.6` | Background tasks and Beat schedule |
| Broker/backend | Redis + redis-py | `redis:7-alpine`, `>=5.0.3` | Celery broker and result backend |
| Browser automation | Selenium | `>=4.18.1` | Remote/local Chrome driver |
| Browser grid | Selenium standalone Chrome | `selenium/standalone-chrome:latest` | Isolated scraping runtime |
| Auth | PyJWT + bcrypt | `>=2.8.0`, `>=4.1.2` | JWT signing and password hashing |
| HTTP client | requests | `>=2.31.0` | Mercado Livre API calls |
| Containers | Docker Compose | Compose file format `3.8` | Local multi-service stack |
| Tests | pytest + pytest-asyncio | Not pinned in `requirements.txt` | Unit and route tests |
| Admin UI | pgAdmin 4 | `dpage/pgadmin4:8` | Local database inspection |

## Architecture

The codebase is a **pragmatic Clean Architecture / DDD layout**: each bounded context owns its model, repository, schemas, use cases, and HTTP routes; infrastructure concerns live under `app/infra`; shared configuration, response formatting, and security live under `app/core`. It is not a pure framework-independent domain: routes are FastAPI routers inside domain packages, and repositories depend on SQLAlchemy. That trade-off keeps the MVP compact while preserving the route → use case → repository direction.

```text
api-price-tracker/
├── alembic/
│   ├── env.py                              # async migration environment, reads app settings
│   └── versions/
│       ├── 0001_initial_tables.py          # user, product_monitored, price_history, audit_log
│       └── 4e006ea0acfe_add_worker_job_table.py
├── app/
│   ├── api/
│   │   ├── deps.py                         # get_db, get_current_user, OAuth2 scheme
│   │   └── endpoints/routes.py             # aggregates every domain router under /api/v1
│   ├── core/
│   │   ├── config.py                       # pydantic-settings, .env loading, DSN assembly
│   │   ├── response.py                     # success_response / error_response envelope
│   │   └── security.py                     # bcrypt + HS256 JWT helpers
│   ├── db/
│   │   ├── base.py                         # model discovery for Alembic metadata
│   │   ├── base_class.py                   # declarative base + automatic snake_case table names
│   │   └── session.py                      # async engine (NullPool) and get_db dependency
│   ├── domain/
│   │   ├── auth/                           # register/login routes + use cases
│   │   ├── user/                           # model, repository, schemas, use cases, /users/me
│   │   ├── product/                        # model, repository, schemas, use cases, CRUD routes
│   │   ├── price_history/                  # history model, repository, response schema
│   │   ├── audit_log/                      # JSONB audit model and repository
│   │   ├── mercado_livre/                  # official API use cases, schemas, routes
│   │   ├── worker/                         # worker_job model, repository, schemas, diagnostics routes
│   │   └── exceptions.py                   # framework-independent domain exceptions
│   ├── helpers/
│   │   ├── price_cleaner.py                # BR/US price string normalization
│   │   └── url_parser.py                   # HTTP(S) URL validation and domain extraction
│   ├── infra/
│   │   ├── clients/mercado_livre_api.py    # OAuth 2.0 + item/product lookup
│   │   ├── logging/logger.py               # structured logging + ContextVars
│   │   ├── scrapers/
│   │   │   ├── base_scraper.py             # scraper interface
│   │   │   └── selenium_scraper.py         # Selenium base + ScraperFactory (registry empty)
│   │   └── worker/
│   │       ├── celery_app.py               # Celery application
│   │       ├── core/celery_config.py       # serialization, time limit, Beat schedule
│   │       ├── tasks/price_check.py        # orchestrate + check tasks
│   │       ├── services/price_check.py     # task orchestration and job status transitions
│   │       ├── runners/price_check.py      # heavy execution with its own DB session
│   │       └── utils/                      # async runner and job-status helpers
│   └── main.py                             # app factory, CORS, middleware, exception handlers
├── tests/                                  # pytest + unittest, external calls mocked
├── docker-compose.yml                      # db, redis, chrome, web, worker, beat, pgadmin
├── Dockerfile                              # python:3.10-slim + build deps
├── requirements.txt                        # runtime lower bounds
├── alembic.ini                             # migration configuration
└── run.py                                  # interactive/CLI developer workflow
```

### Layers and dependency direction

| Layer | Owns | Must not |
|---|---|---|
| `app/domain/*` | Models, schemas, repositories, use cases, and domain routers | Instantiate sessions directly in routes; put SQL in use cases |
| `app/api` | Router aggregation and auth/database dependencies | Contain product or price business rules |
| `app/core` | Settings, security primitives, response envelope | Know about product or worker tables |
| `app/infra` | Celery, Selenium, Mercado Livre client, logging | Be imported by domain schemas or pure helpers |
| `app/db` | Engine, session factory, declarative base | Contain domain behavior |

The intended call direction is **route → use case → repository → SQLAlchemy session**. The current code follows it for user, product, auth, and worker flows. Provider calls are the documented exception: `CheckProductPriceUseCase` invokes the Mercado Livre use case or `ScraperFactory` directly.

### Request and price-check flow

```mermaid
flowchart LR
    C[Client] -->|Bearer JWT| API[FastAPI]
    API -->|CRUD + ownership checks| DB[(PostgreSQL)]
    API -->|create product: best-effort enqueue| R[(Redis)]
    API -->|audit product mutations| DB

    B[Celery Beat] -->|every 60 s| O[orchestrate_price_checks]
    O -->|expired active products, no recent job| DB
    O -->|delay task, then record worker_job| R
    R --> W[Celery Worker]
    W -->|Mercado Livre URL| ML[Mercado Livre official API]
    W -->|other domains| SF[ScraperFactory]
    SF -->|registered scraper| SG[Selenium Grid / Chrome]
    SG --> STORE[Store page]
    W -->|price, price_history, audit_log| DB
    W -->|worker_job status| DB
```

1. The client authenticates at `/api/v1/auth/login` and sends `Authorization: Bearer <token>` on protected routes.
2. `POST /api/v1/products/` creates the product and attempts to enqueue an immediate check. Enqueue failures are swallowed by design, so the product still exists. The enqueue happens before the request-scoped transaction commits, which creates a small visibility window for the worker (documented below).
3. Celery Beat runs `orchestrate_price_checks` every 60 seconds. `ProductRepository.get_expired_for_checking` selects active products whose own `check_interval_minutes` has elapsed and that have no `enqueued`/`processing` job created in the last 10 minutes.
4. Each selected product becomes a `check_product_price_task`. The orchestrator calls `.delay()` and then inserts the `worker_job` row; the task marks that row `processing` when it can find it.
5. `CheckProductPriceUseCase` routes the URL: Mercado Livre domains go to `GetMercadoLivrePriceByUrlUseCase`; every other domain goes through `ScraperFactory`.
6. Success updates `current_price` and `last_checked_at`, appends `price_history(status="success")`, and writes `PRICE_CHECK_SUCCESS` to `audit_log`.
7. Failure still updates `last_checked_at`, appends `price_history(status="failed", error_message=...)`, and writes `PRICE_CHECK_FAILED`. The job ends as `failed` when the result string starts with `failed`.

### Technical decisions

#### 1. Per-product scheduling instead of a global fixed interval

The orchestrator runs every minute, but the SQL filter compares `last_checked_at + check_interval_minutes` against UTC now. A product with a 24-hour interval is not checked every minute; it becomes eligible only after its own interval expires. This keeps Beat simple while honoring per-product configuration.

#### 2. Stale-job guard and duplicate suppression

A `NOT EXISTS` subquery ignores products with an `enqueued` or `processing` job newer than 10 minutes. The 10-minute cutoff prevents an orphaned job from blocking a product forever after a crash or abrupt shutdown. This is a practical mitigation, not a distributed lock: two Beat instances can still race between the `SELECT` and the enqueue.

#### 3. `NullPool` for async sessions

`app/db/session.py` creates the async engine with `NullPool`. FastAPI and Celery create event loops in different contexts; a shared pool can bind connections to a loop that is no longer running. `NullPool` trades some connection reuse for predictability. PostgreSQL should still be sized for the resulting connection churn.

#### 4. Provider routing with an explicit boundary

`_get_price` is the single routing point. Mercado Livre is handled by the official API because it is more stable and cheaper than scraping. Other domains fail fast with a clear error until a scraper class is registered in `ScraperFactory._registry`. This makes the missing-provider state explicit rather than silently returning a wrong price.

#### 5. Response envelope and correlation IDs

Routes return either:

```json
{ "status": "success", "message": "…", "data": {} }
```

or:

```json
{ "status": "error", "message": "…", "details": null }
```

`ENV=production` removes `details` from `error_response`. `X-Correlation-ID` is accepted from the client or generated as a UUID, stored in a `ContextVar`, echoed in the response, and included in every log line as `REQ-xxxxxxxx`. Celery tasks use `TSK-xxxxxxxx`.

#### 6. Authentication is intentionally small

`OAuth2PasswordBearer` points to `/api/v1/auth/login`. Login accepts `username` and `password` as form fields and returns a raw `{"access_token", "token_type": "bearer"}` payload for Swagger/OAuth2 compatibility. Passwords are bcrypt hashes; tokens are HS256 JWTs with `sub` and `exp`. There is no refresh token, revocation list, or refresh rotation.

#### 7. Audit as a first-class table

`audit_log` stores `action`, JSONB `details`, optional `user_id`, optional `ip_address`, and `created_at`. Product create/update/delete and price-check outcomes write audit rows in the same use case that mutates state. This makes failures auditable without relying only on application logs.

### Data model

| Table | Purpose | Key relationships |
|---|---|---|
| `user` | Account identity and bcrypt password hash | Parent of products and audit rows |
| `product_monitored` | Monitored URL, target price, interval, current price, active flag, last check | `user_id` → `user.id` (`ON DELETE CASCADE`) |
| `price_history` | Append-only success/failure observations | `product_id` → `product_monitored.id` (`ON DELETE CASCADE`) |
| `audit_log` | Product and price-check audit trail in JSONB | `user_id` → `user.id` (`ON DELETE SET NULL`) |
| `worker_job` | One row per dispatched Celery task and its status timeline | `product_id` → `product_monitored.id` (`ON DELETE SET NULL`) |

## Quick Start

### Prerequisites

- **Docker Desktop** with Docker Compose (the Compose file uses format `3.8`).
- **Git**.
- **Python 3.10+** only if you want to run `run.py`, Alembic, or the test suite outside the container.
- **Mercado Livre API credentials** (client ID and secret) for live price lookups. Without them, the product CRUD still works, but Mercado Livre checks return a service-unavailable error and are recorded as failures.

### 1. Clone and create the environment file

```powershell
git clone https://github.com/felipevenas/api-price-tracker.git
cd api-price-tracker
Copy-Item .env.example .env
```

On macOS/Linux:

```bash
cp .env.example .env
```

Edit `.env` before starting:

- replace `SECRET_KEY` with a long random value;
- set `MERCADO_LIVRE_CLIENT_ID` and `MERCADO_LIVRE_CLIENT_SECRET` if you need live Mercado Livre data;
- keep the development database values unless you are pointing at another PostgreSQL instance.

`.env.example` contains placeholders only. Never commit `.env` or real credentials.

### 2. Start the full stack

#### Option A — DX script (recommended)

```powershell
python run.py start
```

`run.py` checks whether it is running inside a virtualenv. If not, it creates `.venv`, installs `requirements.txt`, and restarts itself. It then runs `docker-compose up --build -d`, waits for PostgreSQL with `pg_isready`, applies `alembic upgrade head` inside the `web` container (falling back to a local Alembic command), prints container status, and streams logs.

> `run.py` calls the legacy `docker-compose` executable. If your machine only has Compose v2, use Option B or create a `docker-compose` alias.

#### Option B — Docker Compose directly

```powershell
docker compose up --build -d
docker compose exec -T web alembic upgrade head
docker compose logs -f
```

Stop the stack with:

```powershell
docker compose down
```

The named volume `pgdata` preserves PostgreSQL data. `docker compose down -v` deletes it and is intentionally destructive.

#### Option C — local Python process

Use this when you want FastAPI reloads outside Docker while keeping infrastructure in containers:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env

docker compose up -d db redis chrome
alembic upgrade head
uvicorn app.main:app --reload
```

On macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
docker compose up -d db redis chrome
alembic upgrade head
uvicorn app.main:app --reload
```

When running locally, `.env` must point `POSTGRES_SERVER` to `localhost` and `REDIS_URL` to `redis://localhost:6379/0`. The Compose `web` service overrides these values to `db` and `redis://redis:6379/0`.

### 3. Open the local services

| Service | URL / port | Notes |
|---|---|---|
| API | `http://localhost:8000` | FastAPI application |
| Swagger UI | `http://localhost:8000/docs` | Interactive API |
| ReDoc | `http://localhost:8000/redoc` | Alternative API docs |
| OpenAPI JSON | `http://localhost:8000/api/v1/openapi.json` | Schema consumed by clients |
| Health | `http://localhost:8000/health` | Shallow health envelope; not a dependency probe |
| pgAdmin 4 | `http://localhost:8080` | Local-only admin UI |
| Selenium Grid | `http://localhost:4444/wd/hub` | WebDriver endpoint |
| Selenium noVNC | `http://localhost:7900` | Watch Chrome sessions live |
| PostgreSQL | `localhost:5432` | Database |
| Redis | `localhost:6379` | Broker/result backend |

> **Local-only defaults:** `docker-compose.yml` sets PostgreSQL to `postgres/postgres`, pgAdmin to `admin@admin.com/admin`, and the Selenium image uses its default noVNC password. These are development conveniences, not production credentials. Change them before exposing the stack to any shared network.

### 4. Verify the test suite

```powershell
python -m pytest -q
```

The current suite does not require Docker, PostgreSQL, Redis, or network access; external providers are mocked. You need `pytest` and `pytest-asyncio` installed in the environment. They are **not** listed in `requirements.txt`.

## Configuration

Settings are loaded by `pydantic-settings` from `.env` in the working directory, with `case_sensitive=True` and `extra="ignore"`. Environment variables take precedence over the file. `ASYNC_DATABASE_URI` is assembled from the PostgreSQL parts when it is empty.

### Application

| Variable | Required | Default / example | Description |
|---|---|---|---|
| `PROJECT_NAME` | No | `Price Monitor API` | FastAPI title and root response message. |
| `API_V1_STR` | No | `/api/v1` | Prefix for every domain router and the OpenAPI JSON. |
| `ENV` | No | `development` | When exactly `production`, `error_response` drops `details`. Any other value keeps them. |

### Authentication

| Variable | Required | Default / example | Description |
|---|---|---|---|
| `SECRET_KEY` | **Yes** | `SUPER_SECRET_KEY_CHANGE_ME_IN_PRODUCTION` | HS256 signing key. The default is a placeholder and must be replaced in every shared environment. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `10080` (7 days) | Access-token lifetime in minutes. There is no refresh token. |

### PostgreSQL

| Variable | Required | Default / example | Description |
|---|---|---|---|
| `POSTGRES_SERVER` | No | `localhost` (`db` in Compose) | Database host. |
| `POSTGRES_USER` | No | `postgres` | Database user. |
| `POSTGRES_PASSWORD` | No | `postgres` | Database password. Replace outside local development. |
| `POSTGRES_DB` | No | `price_monitor` | Database name. |
| `POSTGRES_PORT` | No | `5432` | Database port. |
| `ASYNC_DATABASE_URI` | No | assembled automatically | Full SQLAlchemy async DSN. Example: `postgresql+asyncpg://postgres:postgres@localhost:5432/price_monitor`. |

### Queue and caching

| Variable | Required | Default / example | Description |
|---|---|---|---|
| `REDIS_URL` | No | `redis://localhost:6379/0` (`redis://redis:6379/0` in Compose) | Celery broker and result backend. |

### Price acquisition

| Variable | Required | Default / example | Description |
|---|---|---|---|
| `SELENIUM_HUB_URL` | No | unset (`http://localhost:4444/wd/hub` in Compose) | When set, the scraper uses a remote WebDriver. When empty, it starts a local headless Chrome. |
| `MERCADO_LIVRE_CLIENT_ID` | For Mercado Livre | placeholder | OAuth 2.0 client ID from the Mercado Livre developer application. |
| `MERCADO_LIVRE_CLIENT_SECRET` | For Mercado Livre | placeholder | OAuth 2.0 client secret. Never commit the real value. |

### Container-only settings

These values are defined directly in [`docker-compose.yml`](docker-compose.yml); they are not read from `.env` by the application.

| Variable | Default | Service | Description |
|---|---|---|---|
| `TZ` | `America/Sao_Paulo` | `db`, `web`, `celery_worker`, `celery_beat`, `pgadmin` | Container timezone. |
| `PGADMIN_DEFAULT_EMAIL` | `admin@admin.com` | `pgadmin` | Local pgAdmin login. |
| `PGADMIN_DEFAULT_PASSWORD` | `admin` | `pgadmin` | Local pgAdmin password. |
| `SE_NODE_MAX_SESSIONS` | `4` | `chrome` | Maximum concurrent Selenium sessions. |
| `SE_NODE_OVERRIDE_MAX_SESSIONS` | `true` | `chrome` | Allows the session limit above to override the image default. |

### Security notes

- Never commit `.env`, JWT values, database passwords, or Mercado Livre secrets.
- `ENV=production` hides error details in the standard error envelope, but route handlers still return HTTP 200 for many domain failures. See [Known Limitations](#known-limitations-mvp-trade-offs).
- The current CORS middleware is hardcoded to `allow_origins=["*"]` with credentials enabled. Restrict it before exposing the API publicly.
- The JWT signing key has no startup validation beyond being a string. A deployment that forgets to replace the placeholder is insecure even though it starts successfully.

## API Surface

Every domain route is mounted under `/api/v1`. The root service banner and `/health` are mounted at the application root. Authentication is `Authorization: Bearer <token>` where the route depends on `get_current_user`.

> **Current worker-route quirk:** `app/domain/worker/routes.py` declares `prefix="/worker"` and `app/api/endpoints/routes.py` includes it again with `prefix="/worker"`. FastAPI concatenates both, so the live paths are `/api/v1/worker/worker/jobs...`. This is a verified current behavior, documented in [Known Limitations](#known-limitations-mvp-trade-offs).

### Service and health

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/` | Public | Service banner with version and project name. |
| `GET` | `/health` | Public | Shallow status envelope. It does not probe PostgreSQL or Redis. |

### Authentication and profile

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/api/v1/auth/register` | Public | Create a user. Returns `201` with the user envelope. |
| `POST` | `/api/v1/auth/login` | Public | OAuth2 password form (`username`, `password`). Returns `access_token` and `token_type` without the envelope. |
| `GET` | `/api/v1/users/me` | Bearer | Read the authenticated profile. |
| `PUT` | `/api/v1/users/me` | Bearer | Update e-mail, full name, password, or active flag. |

### Products and price history

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/api/v1/products/` | Bearer | Create a monitored product and best-effort enqueue an initial check. |
| `GET` | `/api/v1/products/` | Bearer | List the authenticated user's products (`skip`, `limit`). |
| `GET` | `/api/v1/products/{product_id}` | Bearer | Read one owned product. |
| `PUT` | `/api/v1/products/{product_id}` | Bearer | Update name, target price, interval, or active flag. |
| `DELETE` | `/api/v1/products/{product_id}` | Bearer | Delete an owned product (cascades history; audit row is written first). |
| `GET` | `/api/v1/products/{product_id}/history` | Bearer | List price observations (`skip`, `limit`), newest first. |

### Mercado Livre

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/api/v1/mercado-livre/items/{item_id}` | Public in current code | Look up an item or catalog product by `MLB...` ID. |
| `GET` | `/api/v1/mercado-livre/price?url=...` | Public in current code | Extract the `MLB...` ID from a URL and return the current price. |

These routes require `MERCADO_LIVRE_CLIENT_ID` and `MERCADO_LIVRE_CLIENT_SECRET`. Without them, the use case raises `ServiceUnavailableError`, which the route converts into an error envelope. They are currently unauthenticated and should be protected or rate-limited before public exposure.

### Worker diagnostics

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/api/v1/worker/worker/jobs` | Public in current code | List recent jobs, optional `status` filter, `limit` 1–500. |
| `GET` | `/api/v1/worker/worker/jobs/{job_id}` | Public in current code | Read one job by UUID. |
| `GET` | `/api/v1/worker/worker/jobs/product/{product_id}` | Public in current code | List jobs for a product, `limit` 1–200. |

### Query parameters

| Route | Parameter | Type / default | Notes |
|---|---|---|---|
| Product list and history | `skip` | integer, `0` | Offset pagination. |
| Product list and history | `limit` | integer, `100` | No upper bound is enforced. |
| Worker jobs | `status` | enum: `enqueued`, `processing`, `completed`, `failed` | Optional. |
| Worker jobs | `limit` | integer, `100`, min `1`, max `500` | Validated by FastAPI. |
| Worker jobs by product | `limit` | integer, `50`, min `1`, max `200` | Validated by FastAPI. |
| Mercado Livre price | `url` | string, required | Must contain an `MLB...` identifier. |

### Response envelope

Successful domain routes:

```json
{
  "status": "success",
  "message": "Human-readable message",
  "data": {}
}
```

Error envelope:

```json
{
  "status": "error",
  "message": "Human-readable message",
  "details": "Optional technical detail"
}
```

When `ENV=production`, `details` is forced to `null`. Framework-level validation errors return HTTP `422` with the same envelope; unhandled exceptions return HTTP `500`. **Most expected domain failures inside route handlers still return HTTP `200`** because the handler returns `error_response(...)` instead of raising; clients must check `status`, not only the HTTP code.

### Example requests

Register and log in:

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"change-me","full_name":"Example User"}'

curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=change-me"
```

Create a monitored product:

```bash
curl -X POST http://localhost:8000/api/v1/products/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Example product","url":"https://produto.mercadolivre.com.br/MLB-0000000000-example","target_price":1999.90,"check_interval_minutes":60}'
```

List history:

```bash
curl "http://localhost:8000/api/v1/products/$PRODUCT_ID/history?skip=0&limit=50" \
  -H "Authorization: Bearer $TOKEN"
```

## Testing

The suite is **unit and route-level**, with mocked repositories and HTTP clients. It does not start PostgreSQL, Redis, Selenium, or Celery.

```powershell
python -m pytest -q
```

Current result in a clean local Python environment: **24 tests passed**.

| File | What it covers |
|---|---|
| `tests/test_helpers.py` | Brazilian and US price string parsing; URL validation and domain extraction. |
| `tests/test_response.py` | Success envelope, default message, and production detail suppression. |
| `tests/test_mercado_livre_api.py` | `MLB...` extraction, OAuth token success/missing credentials, item price lookup. |
| `tests/test_mercado_livre_domain.py` | Mercado Livre use cases and route envelopes with mocked clients. |
| `tests/test_services_and_usecases.py` | User update, product CRUD use cases, not-found behavior, duplicate e-mail conflict, repository wiring. |

### Test prerequisites

`pytest`, `pytest-asyncio`, and `httpx` are required but are not declared in `requirements.txt`. `httpx` is used by FastAPI's `TestClient`. Install them in your virtualenv:

```powershell
pip install pytest pytest-asyncio httpx
```

### What is not covered

- Real PostgreSQL schema or migration tests.
- Celery worker/Beat execution or Redis integration.
- Selenium scraping against a live page.
- Authentication flow against a live database (register → login → protected route).
- Concurrency behavior of the orchestrator (two Beat instances).

### Continuous integration

There is currently **no `.github/workflows/` directory** in this repository. No CI workflow runs the tests automatically. The quality gate is the local `python -m pytest -q` command until a workflow is added by the maintainer.

## Deployment

This repository does **not** include a production deployment manifest, reverse-proxy configuration, or CI/CD pipeline. The Compose file is a local development/demo stack: it runs Uvicorn with `--reload`, bind-mounts the source tree, publishes database and Selenium ports, and uses development credentials.

A production deployment must supply the following explicitly:

1. **Image** — build from [`Dockerfile`](Dockerfile) (`python:3.10-slim`). The image installs runtime dependencies and copies the repository; it does not define a non-root user or a production command.
2. **Database** — managed or hardened PostgreSQL 15. Set `POSTGRES_*` or `ASYNC_DATABASE_URI`; do not use `postgres/postgres`.
3. **Queue** — reachable Redis 7. Set `REDIS_URL`; do not publish it publicly.
4. **Migrations** — run `alembic upgrade head` as a release step. The API and worker commands do not apply migrations automatically.
5. **Web process** — `uvicorn app.main:app --host 0.0.0.0 --port 8000` (without `--reload`).
6. **Worker process** — `celery -A app.infra.worker.celery_app worker --loglevel=info`.
7. **Beat process** — exactly one `celery -A app.infra.worker.celery_app beat --loglevel=info` per schedule, unless you add a distributed lock. Multiple Beat instances can enqueue duplicate checks.
8. **Scraping runtime** — a Selenium Grid endpoint if you register Selenium scrapers, or unset `SELENIUM_HUB_URL` if you intentionally use local headless Chrome.
9. **TLS and proxy** — terminate TLS in front of the API. The application does not enforce HTTPS or trusted proxy headers.
10. **CORS** — the hardcoded `allow_origins=["*"]` must be replaced with real origins in `app/main.py`; this is a code change, not an environment variable.
11. **Secrets** — inject `SECRET_KEY` and provider credentials from a secret manager, never from a committed file.
12. **Observability** — collect stdout logs (structured context IDs are included) and add external probes. `/health` is shallow and does not verify PostgreSQL or Redis.

### Operational commands

| Task | Command |
|---|---|
| Build image | `docker build -t api-price-tracker .` |
| Apply migrations | `alembic upgrade head` |
| Create revision | `alembic revision --autogenerate -m "description"` |
| Run API | `uvicorn app.main:app --host 0.0.0.0 --port 8000` |
| Run worker | `celery -A app.infra.worker.celery_app worker --loglevel=info` |
| Run Beat | `celery -A app.infra.worker.celery_app beat --loglevel=info` |
| Run tests | `python -m pytest -q` |

## Known Limitations (MVP Trade-offs)

This section is deliberately explicit. These are verified current behaviors, not hidden promises.

### Price acquisition

- **No concrete Selenium scraper is registered.** `ScraperFactory._registry` is empty. Any non-Mercado Livre product URL raises `ValueError` during the check and is recorded as a failed `price_history` row. The Selenium Grid service and base class are scaffolding for future providers.
- **Mercado Livre requires official API credentials.** Without `MERCADO_LIVRE_CLIENT_ID` and `MERCADO_LIVRE_CLIENT_SECRET`, price lookups fail with a service-unavailable error and no price is written.
- **Catalog fallback has a narrow rule.** The client tries `/items/{id}`, then `/products/{id}`. For catalog products without a buy-box price, it checks up to 10 associated offers and picks the lowest positive price. There is no currency conversion.
- **URL handling is permissive.** Product creation accepts any HTTP(S) URL. The only supported provider today is Mercado Livre; other URLs are accepted at write time and fail later during the asynchronous check.

### Scheduling and reliability

- **Beat deduplication is not a distributed lock.** The `NOT EXISTS` guard plus a 10-minute stale threshold reduces duplicates, but two orchestrators running concurrently can still enqueue the same product.
- **Job tracking has an enqueue-before-insert window.** `orchestrate_checks` calls `.delay()` before inserting the `worker_job` row. A fast worker can begin before the row exists, so the `processing` transition may be skipped; the final status update is also conditional on finding the row.
- **The initial check can race the request commit.** Product creation enqueues the first check before the request-scoped database transaction commits. A fast worker can fail to see the product and return `abort_not_found`; the next Beat cycle recovers it because `last_checked_at` is still `NULL`.
- **Aborted checks are marked `completed`.** Only results starting with `failed` map to `JobStatus.failed`. `abort_not_found` (product missing) and `abort_inactive` (product disabled) therefore end as `completed`, even though no price was obtained.
- **The task declares `max_retries=3` but never calls `self.retry`.** A failed check is recorded and left failed; the next eligible interval will try again naturally. There is no exponential backoff.
- **`last_checked_at` is updated on failure too.** This respects the configured interval and avoids hammering a broken provider, but it also means a failed check waits a full interval before retrying.
- **Beat granularity is one minute.** Intervals are configured in whole minutes; sub-minute scheduling is not supported.
- **No dead-letter queue.** Redis is both broker and result backend. Lost tasks are not replayed explicitly; the next Beat cycle is the recovery mechanism.
- **Timezone handling is mixed.** Product scheduling uses UTC-normalized SQL, while Celery and containers are configured for `America/Sao_Paulo`; several model columns use naive `DateTime`. Review timestamp semantics before multi-region deployment.

### API and security

- **Domain errors return HTTP 200.** Route handlers return `error_response(...)` rather than raising, so clients must inspect `status`. Only validation (`422`), framework `HTTPException`, and unhandled exceptions (`500`) use non-2xx codes.
- **Worker diagnostics are duplicated and public.** The live paths are `/api/v1/worker/worker/*` because the prefix is applied twice. The routes do not depend on `get_current_user`, so job metadata is unauthenticated.
- **Mercado Livre routes are public.** They can consume provider quota and expose product metadata without authentication or rate limiting.
- **CORS is wide open.** `allow_origins=["*"]` with `allow_credentials=True` is development-oriented and must be restricted for production.
- **The default `SECRET_KEY` is a placeholder.** The application starts with it; there is no production fail-fast check.
- **JWT lifetime is seven days by default.** There is no refresh token, revocation, logout endpoint, or token rotation.
- **Password policy is minimal.** Minimum length is 6 characters; there is no e-mail verification, MFA, account lockout, or breached-password check.
- **Potential SSRF surface.** Authenticated users can submit arbitrary URLs, and the worker will attempt to fetch them (Mercado Livre API or Selenium). Network egress should be restricted in production.
- **No request rate limiting.** Registration, login, product creation, and provider lookups are unmetered.
- **No soft delete.** Deleting a product removes it and cascades price history. The audit row preserves the action, not the full history.
- **`ENV=production` is exact-match only.** Any other value (including `prod`) leaves technical details visible in error responses.

### Data and operations

- **Pagination is offset-only.** `skip`/`limit` with no total count or cursor; deep offsets degrade on large tables.
- **No history retention or partitioning.** `price_history`, `audit_log`, and `worker_job` grow without an archival policy.
- **`/health` is shallow.** It returns static strings and does not verify PostgreSQL, Redis, Celery, or Selenium.
- **No CI workflow.** Tests, migrations, and image builds are not automated in GitHub Actions.
- **Test coverage is narrow.** There are no database integration tests, Celery tests, Selenium tests, or auth end-to-end tests.
- **Pydantic deprecation warnings.** The current suite emits warnings for class-based `Config` and `json_encoders`; these are forward-compatibility debt, not test failures.
- **Compose is not production-hardened.** It uses `--reload`, source bind mounts, published infrastructure ports, default credentials, and the floating `selenium/standalone-chrome:latest` tag.
- **`run.py` assumes the legacy CLI.** It invokes `docker-compose`, not `docker compose`; environments with only Compose v2 need the direct commands in [Quick Start](#quick-start).
- **Human-readable API messages and OpenAPI tags remain in Portuguese.** Source-level strings were intentionally not modified in this documentation pass.

---

## Governance

This repository follows a formal governance model. **English is the default language for the README, contribution guide, security policy, changelog, code of conduct, and collaboration templates.** Runtime API messages and OpenAPI tags remain in Portuguese until a follow-up source-level translation.

| Document | Purpose |
|---|---|
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Golden rule, setup, branch/commit flow, architecture rules, migrations, and quality gates |
| [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) | Community standards and enforcement guidelines |
| [`SECURITY.md`](SECURITY.md) | Supported versions, private disclosure, security scope, and resolution process |
| [`CHANGELOG.md`](CHANGELOG.md) | Release history ([Keep a Changelog](https://keepachangelog.com/en/1.1.0/) + SemVer) |
| [`LICENSE`](LICENSE) | Proprietary license — all rights reserved |
| [`.github/`](.github) | Issue templates and pull request template |
| [`.editorconfig`](.editorconfig) · [`.gitattributes`](.gitattributes) | LF line endings, UTF-8, and binary normalization |

### Repository standards

- **Workflow:** trunk-based development with short-lived branches merged into `main` through pull requests.
- **Branches:** `feat/`, `bug/`, `chore/`, `docs/`, `style/`, `refactor/`, `test/`.
- **Commits:** Conventional Commits in English (`feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`).
- **Quality gate:** `python -m pytest -q` must pass; new behavior requires tests.
- **Migrations:** never edit an applied revision; generate a new Alembic revision and review the diff before committing.
- **Security:** no secrets in the repository; authorization must be enforced by the API, not only by clients.
- **Documentation:** update the README when routes, environment variables, commands, or limitations change.

## Related Documentation

- [`CONTRIBUTING.md`](CONTRIBUTING.md) — development workflow and architecture rules.
- [`SECURITY.md`](SECURITY.md) — responsible disclosure and security scope.
- [`CHANGELOG.md`](CHANGELOG.md) — version history and release notes.
- [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) — community expectations.
- [`.env.example`](.env.example) — every supported environment variable with safe placeholders.
- [`docker-compose.yml`](docker-compose.yml) — local multi-service topology.
- [`Dockerfile`](Dockerfile) — runtime image definition.
- [`requirements.txt`](requirements.txt) — declared runtime dependencies.
- [`alembic/`](alembic) — schema revisions.
- [`app/infra/scrapers/selenium_scraper.py`](app/infra/scrapers/selenium_scraper.py) — Selenium base class and provider factory.
- [`app/infra/clients/mercado_livre_api.py`](app/infra/clients/mercado_livre_api.py) — Mercado Livre official API client.
- [GitHub repository](https://github.com/felipevenas/api-price-tracker) — source, issues, and security advisories.

## License

**Proprietary** software. All rights reserved. The use, copying, modification, distribution, or commercialization of this software and its documentation is strictly prohibited without prior written permission from the copyright holder. See [`LICENSE`](LICENSE) for the complete terms.

<div align="center">
Built with care by <b><a href="https://github.com/felipevenas">Felipe Venas</a></b>
</div>
