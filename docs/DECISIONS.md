# Architectural Decision Records

## ADR-001: FreeRADIUS Version

**Status:** Proposed
**Date:** 2025-02-09

**Context:** FreeRADIUS has two active branches — 3.2.x (current stable) and 3.0.x (legacy stable). Version 4.0 is in development but not production-ready.

**Decision:** Use FreeRADIUS 3.2.x (latest stable release).

**Rationale:**
- 3.2.x is the actively maintained stable branch
- Most production deployments (including likely at Viasat) run 3.x
- Better SQL module support and bug fixes vs 3.0.x
- 4.0 is too unstable for learning fundamentals

---

## ADR-002: Target OS — Amazon Linux 2023

**Status:** Proposed
**Date:** 2025-02-09

**Context:** Need to choose a base OS for RPM builds and deployment.

**Decision:** Use Amazon Linux 2023 (AL2023) as the target platform.

**Rationale:**
- RPM-based (matches the RPM packaging requirement)
- Native to AWS EC2 (optimized AMIs, no licensing)
- Likely matches or is close to what Viasat uses in AWS
- Modern package versions (gcc, openssl, etc.)

---

## ADR-003: SQL Backend — Start with SQLite

**Status:** Proposed
**Date:** 2025-02-09

**Context:** FreeRADIUS SQL module supports multiple backends (PostgreSQL, MySQL, SQLite). Need to decide on initial backend.

**Decision:** Start with SQLite for Phase 0–3, add RDS PostgreSQL as an enhancement.

**Rationale:**
- SQLite requires zero additional infrastructure
- Faster iteration during learning phases
- FreeRADIUS SQL module interface is the same regardless of backend
- PostgreSQL via RDS adds cost and complexity best deferred to later phases
- Switching backends is a config change, not a code change

---

## ADR-004: RPM Delivery to EC2

**Status:** Accepted
**Date:** 2025-02-09
**Updated:** 2026-02-10

**Context:** Need to get the built RPM artifact from GHA to the EC2 instance.

**Decision:** Upload RPMs to a dedicated S3 bucket from GHA, pull from EC2 using IAM instance profile (Option 2).

**Rationale:**
- Simplest and most AWS-native approach
- No SSH keys or SCP required — aligns with SSM-only access model
- GHA uploads via OIDC/IAM credentials; EC2 pulls via instance profile
- S3 bucket is Terraform-managed with versioning, encryption, and 30-day lifecycle
- Private yum repo (Option 3) adds complexity not warranted for a lab environment

**Implementation:** `terraform/s3.tf` creates `freeradius-lab-rpms-<ACCOUNT_ID>` bucket. EC2 instance role has `s3:GetObject` and `s3:ListBucket` access.

---

## ADR-005: Replace SSM send-command with Ansible

**Status:** Accepted
**Date:** 2026-02-11

**Context:** The deploy pipeline used `aws ssm send-command` to run shell scripts on EC2. This approach was fragile — shell escaping issues, opaque error output, and no idempotency. Configuration management is a relevant skill to demonstrate.

**Decision:** Replace SSM send-command with Ansible, using the `amazon.aws.aws_ssm` connection plugin.

**Rationale:**
- **Idempotency** — `blockinfile`, `systemd`, `dnf` modules are idempotent by design; re-runs produce "ok" not duplicates
- **No SSH required** — SSM connection plugin reuses existing SSM agent + IAM setup, no key management
- **Structured output** — Each task reports ok/changed/failed vs parsing shell exit codes
- **Data-driven** — Users, NAS clients, and test cases defined as YAML variables; adding a test = adding a YAML entry
- **Role-based structure** — Two roles (`freeradius`, `smoke_test`) with defaults, handlers, templates follow Ansible best practices
- **Handlers** — `restart radiusd` only fires when config actually changes

**Trade-offs:**
- Adds Ansible as a dependency (ansible-core, boto3, session-manager-plugin installed in GHA)
- `amazon.aws.aws_ssm` connection is slower than SSH (~2-3s overhead per task for session setup)
- For a lab environment, the reliability and clarity improvements outweigh the speed cost

**Implementation:** `ansible/` directory with roles, playbooks, and dynamic inventory generated from Terraform outputs in GHA.

---

## ADR-006: Observability — Structured Logging + Status-Server (Phase 1)

**Status:** Accepted
**Date:** 2026-02-12

**Context:** The FreeRADIUS lab has zero observability. Logs only exist on ephemeral EC2 instances and are lost on teardown. There's no structured logging, no metrics collection, and no health endpoint. Debugging requires SSM into the instance and reading raw `radius.log`. The observability strategy needs to be built incrementally — starting with FreeRADIUS-native capabilities that require no external dependencies, then layering on shipping (Vector) and a SaaS backend (Grafana Cloud) in later phases.

**Decision:** Implement two FreeRADIUS-native observability primitives as Phase 1:

1. **`rlm_linelog`** — JSON per-request logging to `/var/log/radius/linelog.json`
2. **Status-Server (RFC 5997)** — aggregate counters exposed on UDP 18121 (localhost-only)

Defer Vector agent and Grafana Cloud shipping to Phase 2.

**Rationale:**
- **Zero dependencies** — both are built-in FreeRADIUS modules, no new packages to install or services to manage
- **Immediately useful** — `tail -f linelog.json | jq .` gives live per-request debugging before any shipping pipeline exists
- **Machine-readable from day one** — JSON format is ready for Vector ingestion in Phase 2 without format changes
- **Status-Server is the standard** — RFC 5997 defines it as the health/metrics endpoint for RADIUS servers; `radclient` can query it natively
- **Low risk** — linelog writes to a file, status_server listens on localhost only; neither affects core auth/acct behavior
- **Ansible-managed** — all configuration deployed via the existing `freeradius` role with `radiusd -C` syntax validation as a safety net

**Trade-offs:**
- linelog wiring into `sites-available/default` uses `blockinfile` with `insertafter` regexes that depend on the exact layout of FreeRADIUS 3.2.8's default site config; if upstream changes the format, the regex may not match (mitigated by `radiusd -C` failing the deploy)
- Status-Server secret (`adminsecret`) is a default in role defaults; fine for a lab but should be overridden via secrets for any shared environment
- Log rotation is not yet configured; `/var/log/radius/linelog.json` will grow unbounded until Vector or logrotate is added in Phase 2

**Implementation:** See [OBSERVABILITY.md](OBSERVABILITY.md) for full configuration reference and [OBSERVABILITY_PLAN.md](OBSERVABILITY_PLAN.md) for the multi-phase roadmap.

---

## ADR-007: Container Registry — ghcr.io

**Status:** Accepted
**Date:** 2026-02-13

**Context:** The multi-stage Dockerfile produces a runnable FreeRADIUS runtime image. Currently it only builds locally via `docker compose build`. We need a registry to publish built images so they can be pulled without building from source.

**Decision:** Push images to GitHub Container Registry (ghcr.io) via a dedicated CI workflow, rather than Amazon ECR or Docker Hub.

**Rationale:**
- **Zero cost** — ghcr.io is free for public packages
- **Zero extra secrets** — `GITHUB_TOKEN` has `packages:write` natively; no IAM credentials or Docker Hub tokens to manage
- **Co-located with source** — images appear in the repo's Packages tab, linked to commits
- **Standard tooling** — `docker/login-action`, `docker/build-push-action`, and `docker/metadata-action` are the canonical GHA actions for container CI

**Trade-offs:**
- ECR would keep everything in AWS, closer to the EC2 deployment target; but adds cost (free tier is 500 MB) and requires IAM credentials in GHA
- Docker Hub has broader public reach but requires a separate account and access token secret
- ghcr.io packages default to private; must be manually set to public after first push

**Implementation:** `.github/workflows/docker-image.yml` builds on push to main, tags with short SHA + `latest`, and pushes to `ghcr.io/silverbeer/freeradius-lab`.

---

## ADR-008: Grafana Dashboards & Alerts as IaC

**Status:** Accepted
**Date:** 2026-02-13

**Context:** The observability pipeline (Phases 1-3, 5) ships metrics to Grafana Cloud Mimir and logs to Loki, but there are no dashboards or alert rules. Phase 4 of the observability plan requires implementing these. The dashboards and alerts must survive AWS infrastructure teardown (`terraform destroy`) since the EC2 environment is ephemeral.

**Decision:** Manage Grafana dashboards and alert rules as Terraform resources in a separate root module (`terraform/grafana/`) using the official `grafana/grafana` provider, with a standalone CI workflow.

**Rationale:**
- **Separate root module** — Dashboards persist across AWS `terraform destroy` cycles. The `terraform/` module manages ephemeral AWS infra; `terraform/grafana/` manages persistent Grafana Cloud resources. Same S3 backend, different state key.
- **Terraform over clickops** — Version-controlled, reproducible, diffable. Follows existing repo patterns.
- **Data sources looked up, not created** — Grafana Cloud pre-provisions Prometheus and Loki data sources; creating them in Terraform would conflict.
- **`templatefile()` for dashboard JSON** — Data source UIDs vary per Grafana Cloud stack. Using placeholders (`${prometheus_uid}`, `${loki_uid}`) avoids hardcoding.
- **Separate SA token** — The existing `GRAFANA_API_KEY` is scoped to `metrics:write` + `logs:write` for Vector. Dashboard/alert management requires a Service Account token with Editor role — different permission scope.
- **Standalone CI workflow** — Decoupled from the ephemeral AWS deploy/test/destroy cycle. Triggers on changes to `terraform/grafana/` or `dashboards/`.

**Trade-offs:**
- Requires a second Grafana Cloud credential (`GRAFANA_SA_TOKEN`) alongside the existing `GRAFANA_API_KEY`
- Dashboard JSON files are verbose but can be exported from the UI for iterative development
- Alert rules reference metric/label names that must match the Vector pipeline configuration

**Implementation:** `terraform/grafana/` with provider, backend, data sources, folder, dashboards, and alert rules. Dashboard JSON in `dashboards/`. CI workflow in `.github/workflows/grafana-dashboards.yml`.
