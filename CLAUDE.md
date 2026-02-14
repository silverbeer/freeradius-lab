# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FreeRADIUS lab environment for building, deploying, and testing FreeRADIUS on AWS. The project implements a full lifecycle: **build from source → RPM packaging → infrastructure provisioning → deployment → automated testing → teardown**, all driven by GitHub Actions.

The use case is a "Run Streak Session Tracker" that maps running sessions to RADIUS AAA concepts (authentication, authorization, accounting).

## Architecture

- **Target OS:** Amazon Linux 2023 (AL2023)
- **FreeRADIUS version:** 3.2.x (stable branch)
- **SQL backend:** SQLite initially, with RDS PostgreSQL as a later enhancement
- **Infra:** Terraform-provisioned ephemeral AWS environment (VPC, EC2 for FreeRADIUS, optional RDS)
- **CI/CD:** GitHub Actions pipelines for RPM build, deploy, test, and teardown
- **Config management:** Ansible with `amazon.aws.aws_ssm` connection plugin (no SSH)
- **Observability:** Vector agent on EC2 shipping metrics to Grafana Cloud Mimir and logs to Grafana Cloud Loki
- **Container registry:** ghcr.io for Docker images (built via CI)
- **Tests:** Python (pytest + pyrad) against a live RADIUS server, plus Ansible-driven smoke tests

## Key Technology Choices

| Tool | Purpose |
|------|---------|
| Docker (AL2023-based) | RPM build environment and local runtime |
| Terraform >= 1.5 | AWS infrastructure provisioning |
| Python >= 3.11 + uv | Test suite dependency management |
| pyrad | Python RADIUS client library for tests |
| radtest / radclient | CLI RADIUS testing tools (bundled with FreeRADIUS) |
| Ansible + amazon.aws | Configuration management via SSM (no SSH) |
| Vector 0.43.x | Observability data pipeline (logs + metrics to Grafana Cloud) |

## Common Commands

### RPM Build
```bash
# Build RPM inside Docker container
rpm/build.sh
```

### Docker (local runtime)
```bash
docker compose build          # Build multi-stage image
docker compose up -d           # Start FreeRADIUS container
docker compose down            # Stop container
```

### Terraform
```bash
cd terraform
terraform init
terraform plan
terraform apply
terraform destroy
```

### Ansible (local against EC2)
```bash
# Requires: OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES on macOS
ANSIBLE_CONFIG=ansible/ansible.cfg ansible-playbook ansible/playbooks/deploy.yml \
  -i ansible/inventory/ec2.yml \
  -e rpm_bucket=<bucket> -e rpm_arch=x86_64
```

### Testing
```bash
# Python test suite (run from repo root)
cd tests && uv run pytest

# Run a single test file
cd tests && uv run pytest test_auth.py

# Run a single test
cd tests && uv run pytest test_auth.py::test_valid_user_authenticates
```

### FreeRADIUS
```bash
radiusd -X          # Start in debug mode (foreground, verbose)
radiusd -v          # Check version
radiusd -C          # Verify config syntax
radtest testuser testpass localhost 0 testing123   # Test auth
```

### Grafana Cloud Secrets
```bash
# Verify credentials have write access
./scripts/verify-grafana-secrets.sh

# Push secrets to GitHub repo
./scripts/set-gh-secrets.sh
```

## Repo Layout

- `docs/` — Project plan, RADIUS learning notes, ADRs, observability docs
- `rpm/` — RPM spec file and build helper script
- `docker/` — Multi-stage Dockerfile for build + runtime, docker-compose
- `terraform/` — AWS infrastructure (VPC, EC2, security groups, optional RDS)
- `ansible/` — Ansible roles (freeradius, vector, smoke_test), playbooks, and config
- `cli/` — Custom CLI tools (radcli) for FreeRADIUS operations
- `scripts/` — Helper scripts (set-gh-secrets.sh, verify-grafana-secrets.sh)
- `tests/` — Python test suite (pytest + pyrad) with `pyproject.toml`
- `.github/workflows/` — CI pipelines: `build-rpm.yml`, `deploy-test.yml`, `destroy.yml`, `docker-image.yml`

## Design Decisions

ADRs are tracked in `docs/DECISIONS.md`. Key decisions:
- FreeRADIUS 3.2.x over 3.0.x or 4.0 (ADR-001)
- Amazon Linux 2023 as target platform (ADR-002)
- SQLite first, PostgreSQL later (ADR-003)
- RPM delivery to EC2 via S3 (ADR-004)
- Ansible over SSM replaces shell scripts (ADR-005)
- Vector + Grafana Cloud for observability (ADR-006)
- ghcr.io for container images (ADR-007)

## RADIUS Protocol Basics

- UDP-based: port 1812 (auth), port 1813 (accounting)
- NAS clients authenticate to RADIUS server using shared secrets
- Core data model is Attribute-Value Pairs (AVPs)
- FreeRADIUS request pipeline: authorize → authenticate → post-auth
