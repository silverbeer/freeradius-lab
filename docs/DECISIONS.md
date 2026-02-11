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
