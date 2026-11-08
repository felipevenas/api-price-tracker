# Contributing to Price Tracker API

Thank you for considering a contribution. This document explains how to set up the project, which architectural rules must be preserved, and what a pull request must contain before it can be merged.

**English is the default language for branches, commits, code comments, documentation, issues, and pull requests.** Runtime API messages and OpenAPI tags are still in Portuguese because they live in source strings; do not translate them as part of an unrelated change.

---

## Golden rule

> **No provider lookup is silent.** Every successful or failed provider lookup must leave a `price_history` row and an `audit_log` entry. If you change the price-check flow, preserve that invariant and add a test.

This rule is what makes monitoring debuggable: a missing alert can be distinguished from a provider failure, a bad selector, or a lost task.

---

## Prerequisites

- **Docker Desktop** with Docker Compose.
- **Git**.
- **Python 3.10+** for `run.py`, Alembic, and tests outside the container.
- **Mercado Livre developer credentials** only if you need live price lookups. Unit tests mock the provider.

---

## Local setup

```powershell
git clone https://github.com/felipevenas/api-price-tracker.git
cd api-price-tracker
Copy-Item .env.example .env
python run.py start
```

`run.py start` creates `.venv` when necessary, installs `requirements.txt`, starts the Compose stack, waits for PostgreSQL, applies `alembic upgrade head`, and streams logs.

If you prefer explicit Compose commands:

```powershell
docker compose up --build -d
docker compose exec -T web alembic upgrade head
docker compose logs -f
```

Useful commands:

| Task | Command |
|---|---|
| Start and follow logs | `python run.py start` |
| Stop containers | `python run.py stop` |
| Apply migrations in the `web` container | `python run.py migrate` |
| Follow logs | `python run.py logs` |
| Show container status | `python run.py status` |
| Run tests | `python -m pytest -q` |
| Install test tools | `pip install pytest pytest-asyncio httpx` |

Never commit `.env`. `.env.example` is the only environment file that belongs in Git.

---

## Branch naming

Create short-lived branches from `main` and merge them back through a pull request. Use one of these prefixes:

| Prefix | Use |
|---|---|
| `feat/` | New user-visible capability |
| `bug/` | Bug or security fix |
| `chore/` | Build, dependencies, containers, or tooling |
| `docs/` | Documentation only |
| `style/` | Formatting or log-message changes with no behavior change |
| `refactor/` | Internal restructuring with no behavior change |
| `test/` | Test-only changes |

Examples: `feat/amazon-selenium-scraper`, `bug/timezone-expired-products`, `docs/english-governance`.

Keep the branch focused. Do not mix refactoring, formatting, and behavior changes in the same pull request.

---

## Commit conventions

Use **Conventional Commits in English**, imperative mood, lowercase subject:

```text
feat: add amazon scraper provider
fix: normalize expired product query to UTC
refactor: move price routing into provider function
docs: standardize README and governance in English
test: cover failed price-check history
chore: pin selenium image tag
```

Accepted types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `style`, `perf`, `build`, `ci`.

Rules:

- One logical change per commit.
- Explain **why** in the body when the change is not obvious.
- Reference the issue when one exists (`Refs #123`).
- Never commit secrets, `.env`, generated caches, or local database dumps.

---

## Architecture rules

The project uses a pragmatic Clean Architecture / DDD layout. Preserve the direction **route → use case → repository → SQLAlchemy session**.

### Layer boundaries

| Layer | Allowed | Not allowed |
|---|---|---|
| `app/domain/*/routes.py` | HTTP parsing, dependency injection, translating use-case results into the response envelope | SQL queries, provider calls, or business rules |
| `app/domain/*/usecase.py` | Application rules, ownership checks, orchestration of repositories/providers | FastAPI `Request`/`Response` objects, direct SQL |
| `app/domain/*/repository.py` | SQLAlchemy queries and persistence | HTTP concerns |
| `app/domain/*/model.py` | SQLAlchemy mapping | Business workflows |
| `app/domain/*/schemas.py` | Pydantic contracts and field validation | Database access |
| `app/infra` | Celery, Selenium, external API clients, logging | Being imported by pure helpers or schemas |
| `app/core` | Settings, security primitives, response formatting | Domain-specific workflow logic |

### Provider rules

- Mercado Livre is read through `app/infra/clients/mercado_livre_api.py` and its domain use cases. Do not replace it with a Selenium scraper without a documented reason.
- New Selenium providers must inherit from `SeleniumBaseScraper`, implement `scrape(url) -> Optional[float]`, and be registered in `ScraperFactory._registry` with a focused test.
- A provider must return a positive numeric price or an explicit failure. Never return `0` or a guessed price.
- Do not log tokens, passwords, full `Authorization` headers, or provider secrets.

### Database rules

- Every monitored product belongs to exactly one user. Ownership checks belong in the use case, not only in the route.
- `product_monitored.user_id` cascades on user deletion; `price_history` cascades on product deletion; `audit_log.user_id` is set to `NULL`; `worker_job.product_id` is set to `NULL`.
- Do not add business logic to the declarative base or automatic table-name generation.
- Keep timestamps consistent with the existing UTC/naive convention until a dedicated timezone refactor is approved.

### Response rules

- Use `success_response` and `error_response` from `app/core/response.py` for domain routes.
- Do not expose stack traces, SQL, tokens, or provider payloads in production. `ENV=production` removes `details`, but the route must still avoid putting secrets there.
- New public endpoints must document authentication, rate-limit behavior, and error responses.

---

## Database migrations (Alembic)

When a model changes, generate a revision and commit both the model and the migration:

```powershell
docker compose exec web alembic revision --autogenerate -m "add provider field"
docker compose exec web alembic upgrade head
```

Checklist:

- Review the autogenerated file; Alembic does not detect every constraint or index change.
- Give the revision a meaningful message in English.
- Never edit a migration that has already been applied outside your local environment.
- Include the corresponding `downgrade()` implementation.
- Test `upgrade head` against a clean database before opening the pull request.

---

## Quality gates

Before opening a pull request:

```powershell
python -m pytest -q
```

Requirements:

- All tests pass.
- New behavior has at least one test at the use-case or route level.
- Provider interactions are mocked in unit tests; tests must not require network access.
- No new `DeprecationWarning` from your own code. Existing Pydantic v2 warnings are known debt.
- The application imports successfully: `python -c "from app.main import app; print(len(app.routes))"`.
- If you changed a model, `alembic upgrade head` succeeds on a clean database.

There is currently **no configured linter, formatter, type checker, or CI workflow**. Follow PEP 8, match the surrounding style, and keep functions small. If you introduce a tool, add its configuration and document the command in this file and the README.

---

## Security and privacy

- Never commit real credentials, JWTs, database passwords, Mercado Livre secrets, or `.env`.
- Do not weaken authentication or ownership checks to make a test pass.
- Treat product URLs as untrusted input. The worker may fetch arbitrary HTTP(S) URLs; avoid adding endpoints that let one user probe internal networks.
- Do not log request bodies containing passwords or tokens.
- Report vulnerabilities privately as described in [`SECURITY.md`](SECURITY.md). Do not open a public issue for a suspected vulnerability.

---

## Pull request process

1. Open an issue for non-trivial behavior changes so the approach can be agreed before implementation.
2. Create a branch from `main` using the naming convention above.
3. Implement the change with tests and documentation updates.
4. Run the quality gates locally.
5. Fill in the pull request template completely, including how the change was tested.
6. Keep the pull request focused; split unrelated work.
7. Address review comments with new commits or a documented force-push after review.
8. Squash only when the branch history is noisy; otherwise preserve meaningful commits.

### Definition of Done

- [ ] The change is described and linked to an issue when applicable.
- [ ] `python -m pytest -q` passes.
- [ ] New behavior is covered by tests.
- [ ] Database changes include an Alembic migration and a downgrade path.
- [ ] README and `.env.example` are updated when routes, configuration, or commands change.
- [ ] No secret, token, `.env`, cache, or generated artifact is committed.
- [ ] `CHANGELOG.md` is updated when the change is user-visible.
- [ ] The pull request template is complete and the diff is limited to the intended scope.

---

## Documentation standards

- Write in English, with short paragraphs, tables, and checklists.
- Use backticks for commands, paths, variables, and identifiers.
- Verify every command and version against the repository; do not document aspirational behavior as implemented.
- When a limitation is known, put it in the README's **Known Limitations** section instead of hiding it.
- Fix mojibake and invalid UTF-8 when rewriting a file.

---

## Questions

Open a GitHub Discussion or an issue using the feature request template. For security matters, follow [`SECURITY.md`](SECURITY.md) instead of opening a public issue.
