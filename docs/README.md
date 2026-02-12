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
┌─────────────────────────────────────┐
│  VPC (10.0.0.0/16)                  │
│  ┌────────────────┐  ┌───────────┐  │
│  │ EC2 (AL2023)   │  │ RDS       │  │
│  │ FreeRADIUS     │  │ PostgreSQL│  │
│  │ (RPM install)  │  │ (accounting│ │
│  │ UDP 1812/1813  │  │  & users) │  │
│  └────────────────┘  └───────────┘  │
└─────────────────────────────────────┘
```

## Repo Structure

```
freeradius-lab/
├── README.md
├── docs/
│   ├── PROJECT_PLAN.md          # Phased implementation plan
│   ├── RADIUS_NOTES.md          # Learning notes on RADIUS/AAA
│   ├── DECISIONS.md             # ADRs / design decisions
│   ├── OBSERVABILITY_PLAN.md    # Observability roadmap (Vector + Grafana Cloud)
│   └── OBSERVABILITY.md         # Observability implementation reference
├── rpm/
│   ├── freeradius.spec          # RPM spec file
│   └── build.sh                 # RPM build helper script
├── docker/
│   ├── Dockerfile.build         # RPM build environment (AL2023-based)
│   └── Dockerfile.test          # Local test environment
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── vpc.tf
│   ├── ec2.tf
│   ├── rds.tf
│   └── security_groups.tf
├── ansible/                     # Optional: config management
│   ├── playbook.yml
│   └── roles/
│       └── freeradius/
├── scripts/
│   ├── configure_radius.sh      # Post-deploy FreeRADIUS config
│   ├── seed_test_data.sh        # Populate test users/NAS clients
│   └── smoke_test.sh            # Quick validation
├── tests/
│   ├── conftest.py
│   ├── test_auth.py             # Authentication flow tests
│   ├── test_accounting.py       # Accounting session tests
│   ├── test_authorization.py    # Authorization attribute tests
│   └── pyproject.toml           # Test dependencies (pyrad, pytest)
└── .github/
    └── workflows/
        ├── build-rpm.yml        # Phase 2: RPM build pipeline
        ├── deploy-test.yml      # Phase 4: Full integration pipeline
        └── destroy.yml          # Manual teardown workflow
```

## Quick Start

_Coming soon — see [PROJECT_PLAN.md](docs/PROJECT_PLAN.md) for the phased approach._
