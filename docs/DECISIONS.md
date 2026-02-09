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

**Status:** Proposed
**Date:** 2025-02-09

**Context:** Need to get the built RPM artifact from GHA to the EC2 instance.

**Decision:** TBD — evaluate during Phase 4. Candidates:
1. SCP from GHA runner to EC2
2. Upload to S3, pull from EC2
3. Private yum repo in S3

**Considerations:**
- Option 2 (S3) is simplest and most AWS-native
- Option 3 (yum repo) is most realistic for production patterns
- Option 1 (SCP) requires SSH key management in GHA
