# Security Policy

## Supported versions

Security fixes are applied to the latest release line on `main`. Older snapshots are not maintained.

| Version | Supported |
|---|---|
| `0.3.x` (current: `0.3.1`) | ✅ Yes |
| `< 0.3.1` | ❌ No |

Because this repository is distributed as source, "supported" means the latest commit on `main` and the most recent release. Always deploy from a reviewed commit and keep dependencies updated.

---

## Reporting a vulnerability

**Do not open a public issue for a suspected vulnerability.**

Preferred channel: open a private GitHub Security Advisory at:

**https://github.com/felipevenas/api-price-tracker/security/advisories/new**

Fallback: e-mail **felipevenas@gmail.com** with the subject `[SECURITY] api-price-tracker`.

Please include:

- A clear description of the issue and the affected component or endpoint.
- Reproduction steps or a minimal proof of concept.
- The impact you believe is possible (data exposure, privilege escalation, denial of service, etc.).
- The commit, tag, or environment where you observed it.
- Whether the issue is already public or known to third parties.
- An optional safe contact method and credit preference.

Do not include real user data, production credentials, or third-party personal information. If you must demonstrate a secret leak, redact the value.

---

## Response process

| Stage | Target |
|---|---|
| Acknowledge receipt | Within 48 hours |
| Initial triage and severity assessment | Within 5 business days |
| Fix or mitigation plan | Depends on severity and reproducibility |
| Coordinated disclosure | After a fix is available, by mutual agreement |

The maintainer will:

1. Confirm the report and reproduce it in a private environment.
2. Develop the fix outside the public branch when appropriate.
3. Add or update tests that prove the issue is resolved.
4. Merge the fix into `main` and publish a patch release.
5. Record the security-relevant change in [`CHANGELOG.md`](CHANGELOG.md) without exposing exploitation details before users can upgrade.
6. Credit the reporter if requested and if doing so does not create additional risk.

This is a solo-maintained open-source project. There is **no bug bounty program** and no guaranteed monetary reward. Good-faith reports are appreciated and will be handled transparently.

---

## Security scope

Reports are especially valuable when they affect:

### Authentication and authorization

- JWT forgery, signature bypass, algorithm confusion, or `sub` manipulation.
- Login bypass, password-hash disclosure, or bcrypt misuse.
- Access to another user's products, price history, audit data, or worker jobs (IDOR).
- Privilege escalation through `PUT /api/v1/users/me` or any mass-assignment path.
- Token leakage through logs, error envelopes, or response headers.

### Data protection

- SQL injection or unsafe query construction.
- Exposure of `SECRET_KEY`, database credentials, Mercado Livre client secrets, or full `Authorization` headers.
- Sensitive data returned in `error_response.details` when `ENV=production`.
- Audit-log tampering or omission on product/price mutations.

### Request and provider handling

- Server-side request forgery (SSRF) through product URLs or the Mercado Livre URL parser.
- Unsafe URL schemes, redirect handling, or access to internal metadata services from the worker.
- Denial of service through unbounded pagination, expensive provider calls, or queue flooding.
- Injection into Selenium/CDP commands, browser options, or Celery task payloads.
- Supply-chain issues in unpinned dependencies or the floating Selenium image tag.

### Deployment defaults

- The default `SECRET_KEY` placeholder being used in a reachable environment.
- Wide-open CORS combined with credentials.
- Publicly exposed PostgreSQL, Redis, pgAdmin, Selenium, or noVNC ports.
- Default `postgres/postgres` or pgAdmin credentials reachable from an untrusted network.

### Out of scope

- Vulnerabilities in Mercado Livre, Selenium, PostgreSQL, Redis, Docker, or other third-party services that are not caused by this repository's integration.
- Findings that require a compromised host, physical access, or an already-privileged administrator.
- Volumetric denial of service, spam, or social engineering.
- Missing security headers on a local development stack with no TLS termination.
- Automated scanner output with no reproducible impact.
- Reports about the API intentionally returning HTTP `200` for domain errors. This is documented behavior and a known limitation, not a vulnerability.

---

## Safe harbor

Good-faith security research is welcome. Do not:

- access, modify, or exfiltrate data that does not belong to you;
- test against a production system without written permission;
- degrade availability for other users;
- publish exploitation details before a fix is available.

If you are unsure whether an action is authorized, contact the maintainer first.

---

## Deployment hardening checklist

If you operate this API, at minimum:

- Replace `SECRET_KEY` with a long random value and store it outside Git.
- Set `ENV=production` to suppress technical details in the standard error envelope.
- Replace the hardcoded CORS wildcard in `app/main.py` with explicit origins (requires a code change).
- Use dedicated database and Redis credentials; never publish those ports publicly.
- Run PostgreSQL migrations as a controlled release step.
- Keep `MERCADO_LIVRE_CLIENT_SECRET` in a secret manager.
- Restrict outbound network access from the worker to reduce SSRF impact.
- Put TLS and authentication in front of pgAdmin, Selenium, and noVNC, or keep them off public networks entirely.
- Review [`README.md`](README.md#known-limitations-mvp-trade-offs) for the current security limitations.
