# FreeRADIUS Observability Plan — Vector + Grafana Cloud

## Context

The FreeRADIUS lab has solid functional testing (smoke tests, pytest integration tests) but zero production observability. No structured logging, no metrics collection, no alerting. Logs only exist on the ephemeral EC2 instance and are lost on teardown. This plan adds end-to-end observability using FreeRADIUS native modules, Vector as the on-host agent, and Grafana Cloud (Mimir + Loki) as the SaaS backend.

## Architecture

```
EC2 Instance
┌─────────────────────────────────────────────────────┐
│  FreeRADIUS 3.2.8                                   │
│  ├── linelog module → /var/log/radius/linelog.json   │
│  ├── radius.log     → /var/log/radius/radius.log    │
│  └── status_server  → UDP 18121 (aggregate counters) │
│                                                     │
│  Vector Agent                                       │
│  ├── Sources: linelog, radius.log, host_metrics,    │
│  │            journald, status_server polling        │
│  ├── Transforms: parse JSON, derive metrics,        │
│  │               enrich with labels                 │
│  └── Sinks:                                         │
│       ├── prometheus_remote_write → Grafana Cloud Mimir
│       └── loki                   → Grafana Cloud Loki
└─────────────────────────────────────────────────────┘
```

---

## Phase 1: FreeRADIUS Structured Logging + Status-Server -- COMPLETE

**Status:** Implemented (2026-02-12) — see [OBSERVABILITY.md](OBSERVABILITY.md) for full reference.

**Goal:** Get per-request JSON logs and aggregate counters flowing to files on disk.

### 1A. linelog Module — JSON per-request logging

**New file:** `ansible/roles/freeradius/templates/linelog.j2`

Configures `rlm_linelog` to write one JSON object per line to `/var/log/radius/linelog.json`. Separate message templates for each response type:

- **Access-Accept:** timestamp, type, result, user, nas_ip, nas_id, calling_station, service_type
- **Access-Reject:** timestamp, type, result, user, nas_ip, nas_id, calling_station, module_failure_message
- **Access-Challenge:** timestamp, type, result, user, nas_ip
- **Accounting-Response:** timestamp, type, acct_status, user, session_id, session_time, nas_ip, nas_id

Wire into the default virtual server by adding `linelog` calls to `post-auth` (including `Post-Auth-Type REJECT`) and `accounting` sections via `ansible.builtin.blockinfile`.

### 1B. Enable Status-Server (RFC 5997)

Symlink the existing `sites-available/status` into `sites-enabled/` and set `status_server = yes` in `radiusd.conf`. This exposes aggregate counters on UDP port 18121:

- `FreeRADIUS-Total-Access-Requests`
- `FreeRADIUS-Total-Access-Accepts`
- `FreeRADIUS-Total-Access-Rejects`
- `FreeRADIUS-Total-Access-Challenges`
- `FreeRADIUS-Total-Accounting-Requests`
- `FreeRADIUS-Total-Accounting-Responses`
- `FreeRADIUS-Total-Auth-Duplicated-Requests`
- `FreeRADIUS-Total-Auth-Malformed-Requests`
- `FreeRADIUS-Total-Auth-Invalid-Requests`
- `FreeRADIUS-Total-Auth-Dropped-Requests`

### 1C. Files to change

| File | Change |
|------|--------|
| `ansible/roles/freeradius/templates/linelog.j2` | **New** — linelog module config with JSON format strings |
| `ansible/roles/freeradius/tasks/configure.yml` | Add tasks: deploy linelog, enable module symlink, wire into site config, enable status_server |
| `ansible/roles/freeradius/defaults/main.yml` | Add variables: `freeradius_linelog_path`, `freeradius_status_server_port`, `freeradius_status_server_secret` |

### 1D. Verification

```bash
# After deploy, on EC2 via SSM:
radtest testrunner run123 localhost 0 testing123
tail -1 /var/log/radius/linelog.json | jq .
# Expected: {"timestamp":"...","type":"auth","result":"accept","user":"testrunner",...}

echo "Message-Authenticator = 0x00" | radclient -x 127.0.0.1:18121 status adminsecret
# Expected: FreeRADIUS-Total-Access-Requests = 1, etc.

radiusd -C  # config syntax still valid
```

---

## Phase 2: Vector Agent — Collection + Shipping to Grafana Cloud

**Goal:** Install Vector, configure the pipeline, ship metrics to Mimir and logs to Loki.

### 2A. New Ansible role: `vector`

```
ansible/roles/vector/
  defaults/main.yml        — version, Grafana Cloud endpoints, feature flags
  tasks/main.yml           — orchestration (install → configure → service)
  tasks/install.yml        — add Vector yum repo, install RPM
  tasks/configure.yml      — template vector.yaml, add vector user to radiusd group
  tasks/service.yml        — systemd enable/start, wait for API port 8686
  handlers/main.yml        — restart vector handler
  templates/vector.yaml.j2 — full pipeline config
```

### 2B. Vector Pipeline (vector.yaml.j2)

**Sources (5):**

| Source | Type | What it collects |
|--------|------|-----------------|
| `radius_linelog` | file | `/var/log/radius/linelog.json` — structured request logs |
| `radius_log` | file | `/var/log/radius/radius.log` — standard FreeRADIUS log |
| `host_metrics` | host_metrics | CPU, memory, disk, filesystem, network, loadavg (15s interval) |
| `journald` | journald | systemd journal for `radiusd` and `vector` units |
| `radius_status` | exec | Polls Status-Server via `radclient` every 15s, outputs JSON counters |

**Transforms:**

| Transform | Purpose |
|-----------|---------|
| `parse_linelog` | Parse JSON from linelog file source, add environment/instance labels |
| `derive_auth_metrics` | log_to_metric: `radius_auth_total` counter (by result/user/nas), `radius_acct_total` counter (by acct_status/user) |
| `status_to_metrics` | Convert Status-Server counters to Prometheus gauges (access_requests, accepts, rejects, duplicated, malformed, invalid, dropped) |
| `enrich_radius_log` | Add environment/instance/source labels to standard log entries |
| `enrich_journald` | Add environment/instance/source labels to journal entries |
| `filter_radius_log` | Strip debug-level noise to reduce Loki ingestion cost |

**Sinks (2):**

| Sink | Type | Destination |
|------|------|-------------|
| `grafana_metrics` | prometheus_remote_write | Grafana Cloud Mimir — receives all metrics (auth counters, status counters, host metrics) |
| `grafana_logs` | loki | Grafana Cloud Loki — receives all log streams (linelog, radius.log, journald) |

### 2C. Credentials via GitHub Secrets

Pass as Ansible extra vars (`-e`) from the GitHub Actions workflow. Secrets to configure in the repository:

- `GRAFANA_PROMETHEUS_URL` — e.g., `https://prometheus-prod-XX-XX.grafana.net/api/prom/push`
- `GRAFANA_LOKI_URL` — e.g., `https://logs-prod-XX.grafana.net`
- `GRAFANA_USER` — Grafana Cloud instance user ID
- `GRAFANA_API_KEY` — Grafana Cloud API key

Repository variable: `GRAFANA_CLOUD_ENABLED` ("true" / "false")

### 2D. Files to change

| File | Change |
|------|--------|
| `ansible/roles/vector/*` | **New** — entire role (8 files) |
| `ansible/playbooks/deploy.yml` | Add `vector` role (conditional on `grafana_cloud_enabled`) |
| `.github/workflows/deploy-test.yml` | Pass Grafana Cloud secrets to Ansible, add `enable_observability` workflow input |

### 2E. Verification

```bash
vector --version                              # installed
systemctl status vector                       # running
curl -s http://127.0.0.1:8686/health          # API healthy
journalctl -u vector --no-pager -n 20         # no sink errors
# Check Grafana Cloud Explore → Loki for log streams, Mimir for metrics
```

---

## Phase 3: Health Checks

**Goal:** Comprehensive health checks wired into the existing smoke test role.

### Health Check Inventory

**Process health:**

| Check | Method | What it validates |
|-------|--------|-------------------|
| radiusd process running | `systemctl is-active radiusd` | Process alive |
| radiusd enabled at boot | `systemctl is-enabled radiusd` | Survives reboot |
| Vector process running | `systemctl is-active vector` | Agent alive (conditional) |
| Vector API responding | `curl http://127.0.0.1:8686/health` | Agent healthy (conditional) |

**Network health:**

| Check | Method | What it validates |
|-------|--------|-------------------|
| UDP 1812 listening | `ss -ulnp` (already exists) | Auth port up |
| UDP 1813 listening | `ss -ulnp` (already exists) | Acct port up |
| Status-Server responds | `radclient 127.0.0.1:18121 status` | Internal health endpoint returns counters |

**Logging health:**

| Check | Method | What it validates |
|-------|--------|-------------------|
| linelog file exists | `stat /var/log/radius/linelog.json` | Structured logging active |
| linelog valid JSON | `tail -1 \| jq -e .type` | Format correct |

### Files to change

| File | Change |
|------|--------|
| `ansible/roles/smoke_test/tasks/main.yml` | Add process, status_server, linelog, and Vector health checks |
| `ansible/roles/smoke_test/defaults/main.yml` | Add status_server connection variables |

---

## Phase 4: Alerts

**Goal:** Define alerting rules for Grafana Cloud. Documented in repo for reproducibility.

### Application Log-Level Alerts (Loki LogQL)

| Alert | Query | Condition | Severity |
|-------|-------|-----------|----------|
| Auth Failure Spike | `sum(count_over_time({source="linelog"} \| json \| result="reject" [5m])) > 10` | >10 rejects in 5 min | Warning |
| Unknown NAS Client | `{source="radius_log"} \|= "unknown client"` | Any occurrence | Critical |
| Config Reload Failure | `{source="journald"} \|= "Failed to reload" \|= "radiusd"` | Any occurrence | Critical |
| Module Error | `{source="radius_log"} \|~ "Error\|ERROR" \|~ "rlm_"` | Any occurrence | Warning |
| Duplicate Request Spike | `sum(count_over_time({source="radius_log"} \|= "Dropping duplicate request" [1m])) > 5` | >5 in 1 min | Warning |
| Vector Pipeline Error | `{source="journald", unit="vector"} \|= "error"` | Any occurrence | Warning |

### Metric Alerts (PromQL on Mimir)

| Alert | Expression | Severity |
|-------|-----------|----------|
| Auth Success Rate Low | `1 - (sum(rate(freeradius_radius_auth_total{result="reject"}[5m])) / sum(rate(freeradius_radius_auth_total[5m]))) < 0.8` | Warning |
| Request Rate Zero | `sum(rate(freeradius_radius_auth_total[5m])) == 0 and sum(freeradius_status_access_requests_total) > 0` | Critical |
| FreeRADIUS Down | `absent(freeradius_status_access_requests_total)` | Critical |
| High CPU | `host_cpu_usage_idle < 10` | Warning |
| Disk Space Low | `host_filesystem_free_bytes{mountpoint="/"} / host_filesystem_total_bytes{mountpoint="/"} < 0.1` | Critical |
| Vector Stale | No data received for 5 minutes | Critical |

### System-Level Metrics (from Vector host_metrics)

| Category | Metrics | Why it matters |
|----------|---------|----------------|
| CPU | usage by mode (user, system, idle, iowait) | Crypto operations in EAP-TLS |
| Memory | total, available, buffers | Module memory leaks |
| Disk I/O | read/write bytes | Log write throughput |
| Filesystem | free/total by mountpoint | `/var/log/radius/` filling up |
| Network | rx/tx bytes | UDP traffic volume |
| Load | load1, load5, load15 | Overall system pressure |

### Files to change

| File | Change |
|------|--------|
| `docs/alerts.md` | **New** — full alert definitions with LogQL/PromQL queries |
| `docs/DECISIONS.md` | Add ADR-006: Observability Stack — Vector + Grafana Cloud |

---

## Phase 5: CI Integration

**Goal:** Wire observability into the GitHub Actions pipeline.

### Changes

- Add `enable_observability` boolean workflow input (default: false)
- Pass Grafana Cloud secrets to the Ansible deploy step when enabled
- Pass `grafana_cloud_enabled` to the smoke test step for conditional Vector checks

### Files to change

| File | Change |
|------|--------|
| `.github/workflows/deploy-test.yml` | Add input, pass secrets, conditional checks |

---

## Request-Level Metrics Summary

| Metric | Type | Labels | Source |
|--------|------|--------|--------|
| `freeradius_radius_auth_total` | Counter | result, user, nas_id | linelog via Vector log_to_metric |
| `freeradius_radius_acct_total` | Counter | acct_status, user | linelog via Vector log_to_metric |
| `freeradius_status_access_requests_total` | Gauge | — | Status-Server polling via Vector exec |
| `freeradius_status_access_accepts_total` | Gauge | — | Status-Server polling |
| `freeradius_status_access_rejects_total` | Gauge | — | Status-Server polling |
| `freeradius_status_acct_requests_total` | Gauge | — | Status-Server polling |
| `freeradius_status_auth_duplicated_total` | Gauge | — | Status-Server polling |
| `freeradius_status_auth_malformed_total` | Gauge | — | Status-Server polling |
| `freeradius_status_auth_invalid_total` | Gauge | — | Status-Server polling |
| `freeradius_status_auth_dropped_total` | Gauge | — | Status-Server polling |

---

## Implementation Order

```
Phase 1 (FreeRADIUS linelog + status_server)
  ↓
Phase 2 (Vector agent → Grafana Cloud)  [needs Phase 1 logs to exist]
  ↓
Phase 3 (Health checks in smoke tests)  [needs Phases 1-2 for new checks]
  ↓
Phase 4 (Alert definitions + ADR)       [needs Phase 2 data flowing]
  ↓
Phase 5 (CI wiring)                     [needs Phases 2-3]
```

Each phase is independently valuable:
- **After Phase 1:** `tail -f /var/log/radius/linelog.json | jq .` for live per-request debugging
- **After Phase 2:** Data flows to Grafana Cloud — build dashboards, explore metrics and logs
- **After Phase 3:** Automated health checks catch regressions in CI
- **After Phase 4:** Alerting notifies you of problems when infrastructure is left running
- **After Phase 5:** Full pipeline wired end-to-end through CI

---

## New File Summary

| File | Phase |
|------|-------|
| `ansible/roles/freeradius/templates/linelog.j2` | 1 |
| `ansible/roles/vector/defaults/main.yml` | 2 |
| `ansible/roles/vector/tasks/main.yml` | 2 |
| `ansible/roles/vector/tasks/install.yml` | 2 |
| `ansible/roles/vector/tasks/configure.yml` | 2 |
| `ansible/roles/vector/tasks/service.yml` | 2 |
| `ansible/roles/vector/handlers/main.yml` | 2 |
| `ansible/roles/vector/templates/vector.yaml.j2` | 2 |
| `docs/alerts.md` | 4 |
