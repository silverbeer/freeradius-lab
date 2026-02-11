# Project Plan: FreeRADIUS Lab

## Timeline

Target: Ready to demo/discuss by **Feb 23, 2025** (first day at Viasat).
Working backwards, ~2 weeks of evening/weekend effort.

| Phase | Focus | Target | Est. Effort |
|-------|-------|--------|-------------|
| 0 | Learn & Local Setup | Feb 9–11 | 3–4 hrs |
| 1 | RPM Build from Source | Feb 11–13 | 4–5 hrs |
| 2 | RPM Build Pipeline (GHA) | Feb 13–15 | 3–4 hrs |
| 3 | Terraform: AWS Test Environment | Feb 15–18 | 5–6 hrs |
| 4 | Deploy + Test Pipeline (GHA) | Feb 18–20 | 4–5 hrs |
| 5 | Python Test Suite | Feb 20–22 | 3–4 hrs |
| 6 | Polish & Document | Feb 22–23 | 2–3 hrs |

---

## Phase 0: Learn & Local Setup

**Goal:** Understand RADIUS/AAA fundamentals and get FreeRADIUS running locally.

### Tasks

- [x] Read FreeRADIUS docs: architecture, module system, configuration hierarchy
- [x] Understand RADIUS packet types:
  - `Access-Request` / `Access-Accept` / `Access-Reject`
  - `Accounting-Request` (Start/Stop/Interim-Update)
  - `Acct-Status-Type`, `Acct-Session-Time`, `Acct-Session-Id`
- [x] Run FreeRADIUS in Docker (official `freeradius/freeradius-server` image)
  - Start in debug mode: `radiusd -X`
  - Test with `radtest`: `radtest testuser testpass localhost 0 testing123`
- [x] Explore key config files:
  - `radiusd.conf` — main config
  - `clients.conf` — NAS/client definitions
  - `mods-enabled/` — module configs (sql, eap, etc.)
  - `sites-enabled/` — virtual servers (default, inner-tunnel)
- [x] Document learnings in `docs/RADIUS_NOTES.md`

### Key Concepts to Internalize

- RADIUS is UDP-based (1812 for auth, 1813 for accounting)
- Shared secrets between client (NAS) and server
- Attribute-Value Pairs (AVPs) are the core data model
- FreeRADIUS processes requests through a pipeline: authorize → authenticate → post-auth
- SQL module can store users, groups, and accounting data

### Deliverables

- ~~`docker/Dockerfile.test`~~ — skipped; `docker/Dockerfile.build` serves both build and local experimentation needs
- `docs/RADIUS_NOTES.md` — personal reference notes

---

## Phase 1: RPM Build from Source

**Goal:** Build FreeRADIUS as an RPM package from source, reproducibly.

### Tasks

- [x] Review FreeRADIUS source repo: https://github.com/FreeRADIUS/freeradius-server
  - Identify the stable release branch (3.2.x for production, 3.0.x is legacy)
  - Review existing `redhat/` directory in source — they ship a spec file
- [x] Create build environment:
  - `docker/Dockerfile.build` based on `amazonlinux:2023`
  - Install build deps: `gcc`, `make`, `rpm-build`, `openssl-devel`, `postgresql-devel`, etc.
- [x] Write or adapt RPM spec file (`rpm/freeradius.spec`):
  - Source: download tarball from GitHub release
  - `%prep` — unpack and patch if needed
  - `%build` — `./configure` with appropriate flags + `make`
  - `%install` — `make install DESTDIR=%{buildroot}`
  - `%files` — package the right files
  - Subpackages: consider `freeradius-sql`, `freeradius-utils`
- [x] Build with `rpmbuild` inside the container
- [x] Write `rpm/build.sh` helper script to orchestrate the build
- [x] Validate: install the RPM on a clean AL2023 container and run `radiusd -X`

### Decision Points

- **FreeRADIUS version**: 3.2.x (stable) vs 3.0.x — document rationale in `docs/DECISIONS.md`
- **Use upstream spec file as starting point?** — likely yes, then customize
- **Build deps**: minimal vs full module support — start minimal (SQL + utils)

### Deliverables

- `rpm/freeradius.spec`
- `rpm/build.sh`
- `docker/Dockerfile.build`
- Working RPM artifact

---

## Phase 2: RPM Build Pipeline (GHA)

**Goal:** Automate the RPM build in GitHub Actions, producing a downloadable artifact.

### Tasks

- [x] Create `.github/workflows/build-rpm.yml`:
  - Trigger: push to `main`, PR, manual `workflow_dispatch`
  - Job: spin up AL2023 container, install deps, run `rpm/build.sh`
  - Upload RPM as GHA artifact
- [x] Consider caching:
  - Cache build dependencies (`dnf` packages)
  - Cache source tarball download
- [x] Add basic validation step:
  - Install the built RPM on a clean container
  - Run `radiusd -v` to verify it starts
  - `rpm -qlp` to verify package contents
- [x] Version the RPM:
  - Use git tag or short SHA for release field
  - `freeradius-3.2.x-1.lab.$(git rev-parse --short HEAD).x86_64.rpm`

### Pipeline Design

```yaml
# Simplified structure
name: Build FreeRADIUS RPM
on:
  push:
    branches: [main]
  pull_request:
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    container:
      image: amazonlinux:2023
    steps:
      - checkout
      - install build deps
      - run build.sh
      - upload RPM artifact

  validate:
    needs: build
    runs-on: ubuntu-latest
    container:
      image: amazonlinux:2023
    steps:
      - download RPM artifact
      - install RPM
      - verify radiusd starts
```

### Deliverables

- `.github/workflows/build-rpm.yml`
- Passing CI pipeline producing RPM artifacts

---

## Phase 3: Terraform — AWS Test Environment

**Goal:** IaC to provision an ephemeral FreeRADIUS test environment in AWS.

### Tasks

- [x] Design the environment:
  - VPC with public subnet (keep it simple for lab)
  - EC2 instance (AL2023 AMI, t3.micro) for FreeRADIUS
  - Security group: allow UDP 1812/1813 from test runner, SSH from your IP
  - Optional: RDS PostgreSQL (t3.micro) for SQL backend — or start with SQLite
- [x] Write Terraform modules:
  - `terraform/vpc.tf` — VPC, subnet, IGW, route table
  - `terraform/security_groups.tf` — RADIUS + SSH + RDS access rules
  - `terraform/ec2.tf` — AL2023 instance with user_data for initial setup
  - `terraform/rds.tf` — PostgreSQL instance (optional, can add in Phase 5)
  - `terraform/outputs.tf` — instance IP, RDS endpoint
  - `terraform/variables.tf` — region, instance type, key pair, CIDR blocks
- [x] State management:
  - S3 backend + DynamoDB lock table (standard pattern)
  - Or keep it simple with local state for the lab
- [x] User data script: install RPM, basic config, start radiusd
- [x] Test: `terraform plan` → `terraform apply` → verify SSH + radtest → `terraform destroy`

### Decision Points

- **SQLite vs RDS PostgreSQL** — start with SQLite on the EC2 instance to reduce complexity; add RDS as a later enhancement
- **State management** — S3 backend is more realistic but adds setup overhead; decide based on time
- **Instance sizing** — t3.micro is fine for testing; FreeRADIUS is lightweight

### Deliverables

- Complete Terraform configuration
- Documented `terraform apply` / `terraform destroy` workflow
- `docs/DECISIONS.md` updated with infra choices

---

## Phase 4: Deploy + Test Pipeline (GHA)

**Goal:** End-to-end GHA pipeline: build RPM → provision AWS → deploy → test → teardown.

### Tasks

- [x] Create `.github/workflows/deploy-test.yml`:
  - Trigger: `workflow_dispatch` (manual)
  - **Job 1: Build** — reuse the build-rpm workflow
  - **Job 2: Deploy** — `terraform apply`, Ansible deploy via SSM (no SSH)
  - **Job 3: Test** — Ansible smoke test playbook against the live instance
  - **Job 4: Teardown** — `terraform destroy` (always runs, even on test failure)
- [x] Create `.github/workflows/destroy.yml`:
  - Manual workflow to nuke the environment if something gets stuck
- [x] GHA auth: OIDC (`vars.AWS_ROLE_ARN`) — no static AWS keys or SSH keys needed
- [x] Handle RPM deployment to EC2:
  - Option B chosen: Upload to S3, pull from EC2 via Ansible
- [x] Configure FreeRADIUS post-deploy:
  - Ansible role `freeradius` — install RPM, configure RADIUS, manage service
  - Ansible role `smoke_test` — validate deployment with radtest

### Pipeline Design

```
workflow_dispatch
  │
  ├─► build-rpm (reusable workflow)
  │     └─► artifact: freeradius RPM → S3
  │
  ├─► deploy (needs: build-rpm)
  │     ├─► terraform init + apply
  │     ├─► Ansible deploy playbook via SSM
  │     └─► output: instance ID
  │
  ├─► test (needs: deploy)
  │     ├─► Ansible smoke test playbook
  │     └─► collect results
  │
  └─► teardown (always, needs: deploy)
        └─► terraform destroy
```

### Deliverables

- `.github/workflows/deploy-test.yml`
- `.github/workflows/destroy.yml`
- `ansible/` — roles (`freeradius`, `smoke_test`), playbooks, and inventory
- Working end-to-end pipeline

---

## Phase 5: Python Test Suite

**Goal:** Automated tests that validate FreeRADIUS AAA functionality using the run tracker use case.

### Tasks

- [ ] Set up test project:
  - `tests/pyproject.toml` — dependencies: `pyrad`, `pytest`, `pytest-asyncio`
  - Use `uv` for dependency management
- [ ] Implement test client using `pyrad`:
  - Create a RADIUS client that can send Access-Request and Accounting-Request packets
  - Helper functions for building packets with run-tracker AVPs
- [ ] Write test cases:
  - **`test_auth.py`** — Authentication flows:
    - [ ] Valid user authenticates successfully (Access-Accept)
    - [ ] Invalid password returns Access-Reject
    - [ ] Unknown user returns Access-Reject
    - [ ] Verify response attributes (e.g., Session-Timeout)
  - **`test_accounting.py`** — Accounting session lifecycle:
    - [ ] Accounting-Start creates a session
    - [ ] Accounting-Stop closes a session with duration
    - [ ] Interim-Update works mid-session
    - [ ] Verify session data persisted to SQL backend
  - **`test_authorization.py`** — Authorization attributes:
    - [ ] User gets correct group-based attributes
    - [ ] Rate limiting attributes returned
    - [ ] Custom VSAs (if implemented) returned correctly
- [ ] ~~Add `scripts/smoke_test.sh`~~ — replaced by `ansible/roles/smoke_test/` (done in Phase 4)

### Run Tracker Data Model

Map running concepts to RADIUS attributes:

| Running Concept | RADIUS Attribute | Notes |
|----------------|-----------------|-------|
| Runner ID | User-Name | Runner's username |
| Run start | Acct-Status-Type=Start | Begin accounting session |
| Run end | Acct-Status-Type=Stop | End accounting session |
| Duration (sec) | Acct-Session-Time | Elapsed time of run |
| Distance | Custom VSA or Acct-Output-Octets | Repurpose or use VSA |
| Session ID | Acct-Session-Id | Unique run identifier |
| Device | NAS-Identifier | Running watch/phone |

### Deliverables

- `tests/` directory with passing test suite
- ~~`scripts/smoke_test.sh`~~ — now `ansible/roles/smoke_test/`
- Documented run tracker data model

---

## Phase 6: Polish & Document

**Goal:** Clean up, document, and prepare to discuss/demo at Viasat.

### Tasks

- [ ] Update `README.md` with final architecture and quick start
- [ ] Complete `docs/DECISIONS.md` with all ADRs
- [ ] Review and clean up all code:
  - Consistent formatting, comments, docstrings
  - Remove any hardcoded values or secrets
- [ ] Write a "What I Learned" section in `docs/RADIUS_NOTES.md`
- [ ] Optional enhancements if time permits:
  - [ ] Add RDS PostgreSQL backend (replace SQLite)
  - [ ] Custom FreeRADIUS dictionary for run tracker VSAs
  - [ ] Grafana dashboard for RADIUS metrics (ties into observability story)
  - [ ] `Makefile` or `just` commands for common operations
- [ ] Prepare talking points:
  - What design decisions would change at production scale?
  - How would this approach adapt to Viasat's existing infra?
  - Where would you add observability? (metrics, logs, traces)
  - What would a production CI/CD pipeline look like vs this lab?

---

## Tools & Versions

| Tool | Version | Purpose |
|------|---------|---------|
| FreeRADIUS | 3.2.x | RADIUS server |
| Amazon Linux | 2023 | Target OS (matches likely Viasat env) |
| Terraform | >= 1.5 | Infrastructure provisioning |
| GitHub Actions | N/A | CI/CD pipelines |
| Python | >= 3.11 | Test suite |
| uv | latest | Python dependency management |
| pyrad | latest | Python RADIUS client library |
| radtest | (bundled) | CLI RADIUS testing tool |
| Ansible + amazon.aws | latest | Configuration management via SSM (no SSH) |
| Docker | latest | Local build/test environments |

## References

- [FreeRADIUS Documentation](https://freeradius.org/documentation/)
- [FreeRADIUS Wiki](https://wiki.freeradius.org/)
- [FreeRADIUS GitHub](https://github.com/FreeRADIUS/freeradius-server)
- [RPM Packaging Guide (Fedora)](https://rpm-packaging-guide.github.io/)
- [pyrad Library](https://pypi.org/project/pyrad/)
- [RADIUS RFC 2865](https://tools.ietf.org/html/rfc2865) — Authentication
- [RADIUS RFC 2866](https://tools.ietf.org/html/rfc2866) — Accounting
