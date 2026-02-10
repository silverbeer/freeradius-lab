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
