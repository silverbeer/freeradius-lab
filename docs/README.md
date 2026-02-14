# freeradius-lab

A hands-on lab for building, deploying, and testing [FreeRADIUS](https://freeradius.org/) on AWS — from source to RPM to CI/CD pipeline.

## Why

Pre-start ramp-up project for a role involving CI modernization of a FreeRADIUS-based subscriber terminal AAA service. The goal is to build muscle memory with the full lifecycle: **build from source → RPM packaging → infrastructure provisioning → deployment → automated testing → teardown** — all driven by GitHub Actions.

## Use Case: Run Streak Session Tracker

RADIUS is a session-oriented AAA protocol, which maps naturally to tracking running sessions:

- **Authentication** — runners authenticate before logging activity
- **Authorization** — custom attributes control access (e.g., streak tier)
- **Accounting** — each run is a RADIUS accounting session with start/stop/duration

This exercises FreeRADIUS core features (SQL module, custom dictionaries, accounting) while producing something tangible that could feed data into [myrunstreak.run](https://myrunstreak.run).

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  GitHub Actions Pipeline                            │
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ Build    │→ │ Deploy   │→ │ Test & Validate  │  │
│  │ RPM from │  │ to AWS   │  │ (radtest, pyrad) │  │
│  │ source   │  │ via TF   │  │                  │  │
│  └──────────┘  └──────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────┘

AWS Environment (ephemeral):
┌─────────────────────────────────────────────────────┐
│  VPC (10.0.0.0/16)                                  │
│  ┌────────────────────────────┐                     │
│  │ EC2 (AL2023)               │                     │
│  │ FreeRADIUS (RPM install)   │                     │
│  │ Vector → Grafana Cloud     │                     │
│  │ UDP 1812/1813/18121        │                     │
│  └────────────────────────────┘                     │
└─────────────────────────────────────────────────────┘
```

## Repo Structure

```
freeradius-lab/
├── docs/
│   ├── PROJECT_PLAN.md          # Phased implementation plan
│   ├── RADIUS_NOTES.md          # Learning notes on RADIUS/AAA
│   ├── DECISIONS.md             # ADRs / design decisions
│   ├── OBSERVABILITY_PLAN.md    # Observability roadmap (Vector + Grafana Cloud)
│   ├── OBSERVABILITY.md         # Observability implementation reference
│   └── DEPLOY_ISSUES.md         # Deploy pipeline issue tracker
├── rpm/
│   ├── freeradius.spec          # RPM spec file
│   └── build.sh                 # RPM build helper script
├── docker/
│   └── Dockerfile               # Multi-stage: RPM build + runtime image
├── terraform/
│   ├── main.tf, vpc.tf, ec2.tf  # AWS infrastructure
│   └── bootstrap/               # One-time S3/DynamoDB state backend setup
├── ansible/
│   ├── playbooks/               # deploy.yml, smoke_test.yml, deploy-docker.yml
│   ├── roles/
│   │   ├── freeradius/          # Install, configure, start FreeRADIUS
│   │   ├── vector/              # Install, configure Vector → Grafana Cloud
│   │   └── smoke_test/          # Health checks and validation
│   └── inventory/               # EC2 (SSM) and Docker inventories
├── cli/                         # Custom CLI tools (radcli)
├── scripts/
│   ├── set-gh-secrets.sh        # Push .gh-secrets to GitHub repo secrets
│   └── verify-grafana-secrets.sh # Verify Grafana Cloud credentials
├── tests/
│   ├── test_auth.py             # Authentication flow tests
│   ├── test_accounting.py       # Accounting session tests
│   ├── test_authorization.py    # Authorization attribute tests
│   └── pyproject.toml           # Test dependencies (pyrad, pytest)
├── .gh-secrets.example          # Template for Grafana Cloud credentials
├── docker-compose.yml           # Local FreeRADIUS runtime
└── .github/workflows/
    ├── build-rpm.yml            # RPM build pipeline
    ├── deploy-test.yml          # Full integration pipeline (build → deploy → test)
    ├── destroy.yml              # Manual teardown workflow
    └── docker-image.yml         # Build and push Docker image to ghcr.io
```

## Quick Start

### Local (Docker)
```bash
docker compose up -d --build     # Build and start FreeRADIUS
radtest testuser testpass localhost 0 testing123   # Test auth
```

### CI Pipeline
1. Set up AWS OIDC role and Terraform state backend (see `terraform/bootstrap/`)
2. Copy `.gh-secrets.example` to `.gh-secrets`, fill in Grafana Cloud credentials
3. Run `./scripts/verify-grafana-secrets.sh` to verify credentials
4. Run `./scripts/set-gh-secrets.sh` to push secrets to GitHub
5. Trigger the **Deploy & Test** workflow from the Actions tab

### Local Ansible (against EC2)
```bash
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES   # macOS only
ANSIBLE_CONFIG=ansible/ansible.cfg ansible-playbook ansible/playbooks/deploy.yml \
  -i ansible/inventory/ec2.yml \
  -e rpm_bucket=<your-bucket> -e rpm_arch=x86_64
```
