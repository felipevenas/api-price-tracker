# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Documentation

- Standardized `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `CHANGELOG.md`, and the new `CODE_OF_CONDUCT.md` in English, fixing UTF-8/mojibake corruption.
- Added GitHub pull request and issue templates under `.github/`.
- Translated `.env.example` comments and placeholder values to English without adding secrets.
- Documented the verified architecture, environment variables, routes, testing commands, deployment requirements, and known limitations.
- Clarified that Mercado Livre prices are currently read through the official API and that no concrete Selenium scraper is registered.

## [0.3.1] - 2026-07-25

### Fixed

- **Price-check orchestration**
  - Fixed the timezone mismatch in the expired-product selection query in `ProductRepository.get_expired_for_checking`, normalizing the current date to naive UTC with `func.timezone('utc', func.now())`.
  - Prevented duplicate queue tasks by filtering out products with active jobs (`enqueued` or `processing`) using a `NOT EXISTS` clause.
  - Handled orphaned/stuck jobs by limiting the active-job check to records created in the last 10 minutes, preventing a product from being blocked indefinitely after startup or an abrupt shutdown.

## [0.3.0] - 2026-07-23

### Added

- **Standardized response module**
  - Added `app/core/response.py` with `success_response` and `error_response`.
  - Added the corresponding test suite in `tests/test_response.py`.

### Refactored

- **API route standardization**
  - Replaced raw returns and `HTTPException` usage with standardized success and error envelopes across every domain route: `auth`, `mercado_livre`, `product`, `user`, and `worker`.
  - Updated the `/` and `/health` endpoints in `app/main.py` to return the new envelope.
  - Added a global exception handler that captures unexpected exceptions and returns the standardized response with status `500`.
  - Updated the corresponding tests in `tests/test_mercado_livre_domain.py`.

## [0.2.0] - 2026-07-21

### Refactored

- **CRUD naming standardization and Clean Architecture refactor**
  - Removed anemic `service.py` classes in favor of use cases focused on application actions.
  - Added domain-specific use cases in `app/domain/user/usecase.py`, `app/domain/auth/usecase.py`, and `app/domain/product/usecase.py`, orchestrating repositories directly.
  - Standardized repository method names (`get_by_user`, `get_by_product`, `get_expired_for_checking`).
  - Applied dependency injection with `Depends` at the top of each route module and in `app/api/deps.py`.

## [0.1.0] - 2026-07-20

### Added

- **Base architecture (Clean Architecture + DDD)**
  - Initialized the directory structure separating Domain (User, Product, Price History, Audit Log), API (endpoints, middleware, and dependencies), and Infrastructure (queue, logging, and scrapers).
  - Implemented the SQLAlchemy declarative base with dynamic table-name mapping.
- **User domain and authentication**
  - Modeled the `user` table with UUID primary keys and indexes.
  - Implemented secure password hashing with `bcrypt` and JWT generation/validation.
  - Added `/auth/register` and `/auth/login` routes, including Swagger-compatible authentication.
  - Added the protected `/users/me` route for reading and updating profile data through the `get_current_user` dependency.
- **Product domain and price history**
  - Modeled and created the `product_monitored` table with a custom check interval and active/inactive status.
  - Created the `price_history` table to track price changes and record failures.
  - Implemented product CRUD orchestration through repositories and services.
- **Audit and traceability**
  - Modeled the `audit_log` table using PostgreSQL `JSONB` for dynamic audit metadata.
  - Added audit records for critical product actions: creation, update, and deletion.
- **Selenium Grid scraping foundation**
  - Created the base scraper infrastructure with support for the Docker Selenium Grid (`chrome:4444`).
  - Added an initial Mercado Livre scraper prototype with explicit waits and anti-bot patches (CDP `navigator.webdriver` override and headful rendering inside the virtual display).
  - Added helper modules: `price_cleaner` for monetary string conversion and `url_parser` for domain extraction and validation.
- **Structured logging**
  - Configured logging with asynchronous `ContextVar` values.
  - Injected unified context identifiers into logs: `REQ-xxxx` for HTTP requests through FastAPI middleware and `TSK-xxxx` for Celery background tasks.
- **Queueing and scheduling (Celery + Redis + Beat)**
  - Configured Celery with Redis as both broker and result backend.
  - Added the periodic `orchestrate_price_checks` task (Celery Beat) to find products with an expired check interval every minute.
  - Added the `check_product_price_task` worker task to load Selenium, scrape asynchronously, update the database, and persist the price observation.
- **Developer experience script**
  - Added the interactive `run.py` script to start the stack, rebuild images, apply Alembic migrations, and display real-time logs and container status.
- **Pytest suite**
  - Configured unit tests validating price-string cleaning helpers and URL validators.
