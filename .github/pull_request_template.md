# Pull Request

## Description

<!-- Describe the change, the motivation, and the problem it solves. Link the related issue when applicable. -->

Refs:

## Type of change

- [ ] `feat` — new feature
- [ ] `fix` — bug fix
- [ ] `refactor` — internal change without behavior change
- [ ] `docs` — documentation only
- [ ] `style` — formatting or log-message change
- [ ] `test` — test-only change
- [ ] `chore` — build, dependency, container, or tooling change

## How was it tested?

<!-- Describe the commands and scenarios you ran. Include relevant output, not only "it works". -->

- [ ] `python -m pytest -q` passes.
- [ ] The application imports successfully: `python -c "from app.main import app; print(len(app.routes))"`.
- [ ] Docker Compose stack started and the affected flow was exercised manually.
- [ ] Alembic migration created and applied on a clean database (if applicable).
- [ ] Celery worker/Beat behavior verified (if applicable).
- [ ] New or changed endpoint tested through Swagger or `curl`.
- [ ] Other:

## Evidence

<!-- Paste relevant logs, request/response envelopes, screenshots of Swagger/pgAdmin, or the Celery task output. Redact secrets and personal data. -->

## Checklist

- [ ] I followed the architecture rules in `CONTRIBUTING.md`.
- [ ] I kept the route → use case → repository direction.
- [ ] I added or updated tests for the new behavior.
- [ ] I updated `README.md` and `.env.example` when routes, configuration, or commands changed.
- [ ] I updated `CHANGELOG.md` for user-visible changes.
- [ ] I added an Alembic migration and downgrade path for model changes.
- [ ] I did not commit `.env`, credentials, tokens, caches, or generated artifacts.
- [ ] I reviewed my own diff and removed unrelated changes.
- [ ] I considered security and privacy impact (authentication, ownership, SSRF, secret exposure).
- [ ] The pull request is focused on a single logical change.
