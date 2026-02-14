# Deploy Pipeline Issues — Root Cause Analysis

## Background

The `deploy-test.yml` GitHub Actions workflow runs: **build RPMs → provision EC2 → upload RPMs to S3 → run Ansible to install/configure FreeRADIUS → test**. Multiple issues were discovered and resolved during the initial bringup.

## Issue 1: dnf "conflicting requests" error — RESOLVED

**Where it failed:** Ansible task "Install FreeRADIUS RPMs" in `ansible/roles/freeradius/tasks/install.yml`

**Error:**
```
Depsolve Error: cannot install both
  freeradius-3.2.8-1.lab.cce5b005...amzn2023.x86_64 and
  freeradius-3.2.8-1.lab.49ce3c7a...amzn2023.x86_64
```

**Root cause:** The S3 bucket accumulates RPMs across CI runs. Each build stamps a unique git SHA into the RPM filename. When Ansible downloads from S3, multiple versions of the same package exist and `dnf` cannot install them simultaneously.

**Fix:** Rewrote `install.yml` to flatten S3 subdirectories and deduplicate RPMs by keeping only the latest per package before running `dnf install`.

## Issue 2: Ansible crashes on macOS with fork() error — RESOLVED (workaround)

**Where it failed:** Immediately on `ansible-playbook` invocation — the `Gathering Facts` task never completes.

**Error:**
```
[ERROR]: A worker was found in a dead state
Application Specific Information: crashed on child side of fork pre-exec
```

**Root cause:** The `amazon.aws.aws_ssm` connection plugin uses Python's `fork()` to spawn SSM sessions. On macOS, the Objective-C runtime aborts processes that call Objective-C APIs in a forked child.

**Fix:** Set `OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES` before running `ansible-playbook`. This is the standard workaround across the Ansible community for macOS + SSM. Does not affect CI (Ubuntu runners).

```bash
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
ANSIBLE_CONFIG=ansible/ansible.cfg ansible-playbook ansible/playbooks/deploy.yml -i ansible/inventory/ec2.yml ...
```

## Issue 3: find didn't recurse into subdirectories — RESOLVED

**Fix:** Added `recurse: true` to the `ansible.builtin.find` task (commit `49ce3c7`), then rewrote to flatten subdirs in the download step itself.

## Issue 4: ansible_become disabled by inventory merge — RESOLVED

**Where it failed:** Ansible task "Install FreeRADIUS RPMs" — `dnf install` ran without root privileges.

**Error:**
```
Error: This command has to be run with superuser privileges (under the root user on most systems).
```

**Root cause:** The GHA workflow used `-i ansible/inventory/` (directory), which loaded all inventory files including `docker.yml`. That file sets `ansible_become: false` for the `freeradius` host, which overrode the play-level `become: true` and prevented sudo escalation for all tasks.

**Fix:** Changed the workflow to use `-i ansible/inventory/inventory.aws_ssm.yml` (specific file) instead of the directory, so `docker.yml` is not loaded during AWS deployments.

## Issue 5: RADIUS port checks used TCP instead of UDP — RESOLVED

**Where it failed:** Ansible task "Verify RADIUS ports are listening" — `wait_for` timed out.

**Root cause:** `ansible.builtin.wait_for` checks TCP by default, but RADIUS uses UDP (ports 1812, 1813, 18121).

**Fix:** Replaced `wait_for` with `ss -ulnp | grep` checks with retries.

## Issue 6: Vector health check timeout — RESOLVED

**Where it failed:** Ansible task "Wait for Vector API health port" — port 8686 never responded.

**Root cause:** Two issues: (1) Vector's API is disabled by default — needed `api: enabled: true` in config. (2) When reusing an EC2 instance, config changes trigger a handler restart that runs at end-of-play (after the health check).

**Fix:** Added `api: enabled: true` to `vector.yaml.j2` and added `meta: flush_handlers` before the health check to restart Vector with the new config before checking the port.

## Issue 7: Grafana Cloud authentication failures — RESOLVED

**Where it failed:** Vector logs showed `401 Unauthorized` on both Prometheus and Loki sinks.

**Root cause:** Three issues discovered:
1. Prometheus and Loki have **different instance IDs** in Grafana Cloud — a single `GRAFANA_USER` doesn't work for both
2. The initial API key was a **read-only Loki key** — Vector needs write access
3. The `set-gh-secrets.sh` script used `IFS='='` to parse the secrets file, which truncated API keys containing base64 `=` padding characters

**Fix:** Split `GRAFANA_USER` into `GRAFANA_PROMETHEUS_USER` and `GRAFANA_LOKI_USER`. Generated a Grafana Cloud Access Policy token with `metrics:write` and `logs:write` scopes. Fixed scripts to use `${line%%=*}` / `${line#*=}` parameter expansion instead of `IFS='='`.
