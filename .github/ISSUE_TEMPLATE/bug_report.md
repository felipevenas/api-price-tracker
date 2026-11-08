---
name: Bug report
about: Report a reproducible problem in the API, worker, scheduler, or scraping flow.
title: 'bug: [short description]'
labels: bug
assignees: ''
---

## Problem

<!-- A clear and concise description of the bug. What is broken, and where? -->

## Steps to reproduce

1. Environment (Docker Compose, local Python, or deployed instance):
2. Endpoint or command used:
3. Request payload or parameters (redact tokens and personal data):
4. Observed result:
5. Relevant logs (`python run.py logs`, Celery worker output, or FastAPI traceback):

## Expected behavior

<!-- What did you expect to happen? -->

## Actual behavior

<!-- What happened instead? Include the response envelope and HTTP status. -->

## Impact and scope

- Affected version or commit:
- Affected component: API / Celery worker / Celery Beat / PostgreSQL / Redis / Selenium / Mercado Livre integration / other
- Is the issue reproducible consistently?
- Does it affect authentication, authorization, or data isolation?
- Could it expose secrets, personal data, or internal network access?

> If this is a security vulnerability, **do not continue here**. Follow `SECURITY.md` and report it privately.

## Environment

- OS:
- Python version:
- Docker / Compose version:
- PostgreSQL version:
- Redis version:
- Selenium image or browser version:
- Deployment type:

## Additional context

<!-- Add logs, correlation IDs, screenshots, or hypotheses. Redact secrets. -->
