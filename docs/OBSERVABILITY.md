# FreeRADIUS Observability — Implementation Reference

This document describes the observability capabilities deployed to the FreeRADIUS lab, how they work, and how to use them. Updated as each phase is implemented.

See also:
- [OBSERVABILITY_PLAN.md](OBSERVABILITY_PLAN.md) — multi-phase roadmap
- [DECISIONS.md](DECISIONS.md) — ADR-006 for the design rationale

---

## Phase 1: Structured Logging + Status-Server

Deployed via the `freeradius` Ansible role. No external dependencies.

### Structured JSON Logging (rlm_linelog)

Every RADIUS request that produces a reply generates a single JSON line in `/var/log/radius/linelog.json`. This is powered by FreeRADIUS's built-in `rlm_linelog` module.

#### How It Works

```
RADIUS request → FreeRADIUS processing → reply generated
                                              ↓
                                    post-auth / accounting section
                                              ↓
                                    linelog module writes JSON line
                                              ↓
                                    /var/log/radius/linelog.json
```

The `reference` directive dispatches to a different JSON format based on the reply packet type:

```
reference = "messages.%{%{reply:Packet-Type}:-default}"
```

This means Access-Accept replies use the `messages.Access-Accept` template, rejects use `messages.Access-Reject`, and so on. Unrecognized packet types fall through to `messages.default`.

#### Log Formats by Packet Type

**Access-Accept** (successful authentication):
```json
{
  "timestamp": "2026-02-12T14:30:00.000000+0000",
  "type": "auth",
  "result": "accept",
  "user": "testrunner",
  "nas_ip": "10.0.1.50",
  "nas_id": "lab-test",
  "calling_station": "192.168.1.100",
  "service_type": "Framed-User"
}
```

**Access-Reject** (failed authentication):
```json
{
  "timestamp": "2026-02-12T14:30:05.000000+0000",
  "type": "auth",
  "result": "reject",
  "user": "baduser",
  "nas_ip": "10.0.1.50",
  "nas_id": "lab-test",
  "calling_station": "192.168.1.100",
  "module_fail_msg": "No such user"
}
```

**Access-Challenge**:
```json
{
  "timestamp": "2026-02-12T14:30:10.000000+0000",
  "type": "auth",
  "result": "challenge",
  "user": "eapuser",
  "nas_ip": "10.0.1.50"
}
```

**Accounting-Response**:
```json
{
  "timestamp": "2026-02-12T14:30:15.000000+0000",
  "type": "acct",
  "acct_status": "Start",
  "user": "testrunner",
  "session_id": "abc123",
  "session_time": "",
  "nas_ip": "10.0.1.50",
  "nas_id": "lab-test"
}
```

**Default** (any other packet type):
```json
{
  "timestamp": "2026-02-12T14:30:20.000000+0000",
  "type": "unknown",
  "packet_type": "CoA-ACK",
  "user": "testrunner"
}
```

#### Field Reference

| Field | FreeRADIUS Expansion | Present In | Description |
|-------|---------------------|------------|-------------|
| `timestamp` | `%S` | All | ISO 8601 timestamp with microseconds |
| `type` | (hardcoded) | All | `"auth"`, `"acct"`, or `"unknown"` |
| `result` | (hardcoded) | Auth types | `"accept"`, `"reject"`, or `"challenge"` |
| `user` | `%{User-Name}` | All | The authenticating username |
| `nas_ip` | `%{NAS-IP-Address}` | All | IP of the NAS (network access server) sending the request |
| `nas_id` | `%{NAS-Identifier}` | Accept, Reject, Acct | NAS identifier string |
| `calling_station` | `%{Calling-Station-Id}` | Accept, Reject | Client device identifier (usually IP or MAC) |
| `service_type` | `%{Service-Type}` | Accept | Requested service type (e.g., Framed-User) |
| `module_fail_msg` | `%{Module-Failure-Message}` | Reject | Reason for rejection from the failing module |
| `acct_status` | `%{Acct-Status-Type}` | Acct | Accounting event: Start, Stop, Interim-Update |
| `session_id` | `%{Acct-Session-Id}` | Acct | Unique session identifier |
| `session_time` | `%{Acct-Session-Time}` | Acct | Session duration in seconds (present on Stop/Interim-Update) |
| `packet_type` | `%{reply:Packet-Type}` | Default | Raw packet type for unrecognized replies |

#### Where It's Wired In

The `linelog` module is called in three sections of the `sites-available/default` virtual server:

1. **`post-auth {}`** — logs Access-Accept and Access-Challenge replies
2. **`Post-Auth-Type REJECT {}`** — logs Access-Reject replies
3. **`accounting {}`** — logs Accounting-Response replies

These are inserted via `ansible.builtin.blockinfile` with unique markers so they can be updated idempotently.

#### File Details

| Property | Value |
|----------|-------|
| Path | `/var/log/radius/linelog.json` |
| Owner | `radiusd:radiusd` |
| Dir permissions | `0750` |
| File permissions | `0640` |
| Format | NDJSON (one JSON object per line, newline-delimited) |
| Rotation | Not yet configured (planned for Phase 2 with Vector) |

#### Debugging with linelog

```bash
# Live tail with pretty-printing
tail -f /var/log/radius/linelog.json | jq .

# Show only rejects
tail -f /var/log/radius/linelog.json | jq 'select(.result == "reject")'

# Count requests by result type
jq -r '.result // .type' /var/log/radius/linelog.json | sort | uniq -c | sort -rn

# Show all requests for a specific user
jq 'select(.user == "testrunner")' /var/log/radius/linelog.json

# Show accounting session flow
jq 'select(.type == "acct")' /var/log/radius/linelog.json

# Last 5 entries, one per line
tail -5 /var/log/radius/linelog.json | jq -c .
```

---

### Status-Server (RFC 5997)

FreeRADIUS's built-in health and metrics endpoint. Exposes aggregate counters for all requests processed since the last restart. Accessible only from localhost.

#### How It Works

```
radclient query (localhost:18121) → FreeRADIUS status virtual server
                                          ↓
                                  returns Access-Accept with
                                  aggregate counter AVPs
```

The Status-Server is a separate virtual server (`sites-available/status`) that responds to `Status-Server` packets with a set of `FreeRADIUS-Total-*` attributes containing cumulative counters.

#### Querying the Status-Server

```bash
# Full status query
echo "Message-Authenticator = 0x00" | radclient -x 127.0.0.1:18121 status adminsecret
```

Expected output:
```
Received Access-Accept Id 123 from 127.0.0.1:18121 to 127.0.0.1:xxxxx length XX
    FreeRADIUS-Total-Access-Requests = 42
    FreeRADIUS-Total-Access-Accepts = 38
    FreeRADIUS-Total-Access-Rejects = 4
    FreeRADIUS-Total-Access-Challenges = 0
    FreeRADIUS-Total-Auth-Responses = 42
    FreeRADIUS-Total-Auth-Duplicated-Requests = 0
    FreeRADIUS-Total-Auth-Malformed-Requests = 0
    FreeRADIUS-Total-Auth-Invalid-Requests = 0
    FreeRADIUS-Total-Auth-Dropped-Requests = 0
    FreeRADIUS-Total-Auth-Unknown-Types = 0
    FreeRADIUS-Total-Accounting-Requests = 10
    FreeRADIUS-Total-Accounting-Responses = 10
```

#### Available Counters

| Counter | Description |
|---------|-------------|
| `FreeRADIUS-Total-Access-Requests` | Total auth requests received |
| `FreeRADIUS-Total-Access-Accepts` | Successful authentications |
| `FreeRADIUS-Total-Access-Rejects` | Failed authentications |
| `FreeRADIUS-Total-Access-Challenges` | EAP/multi-step auth challenges sent |
| `FreeRADIUS-Total-Auth-Responses` | Total auth responses sent |
| `FreeRADIUS-Total-Auth-Duplicated-Requests` | Duplicate requests (retransmissions from NAS) |
| `FreeRADIUS-Total-Auth-Malformed-Requests` | Requests that failed to parse |
| `FreeRADIUS-Total-Auth-Invalid-Requests` | Requests with bad authenticator or unknown NAS |
| `FreeRADIUS-Total-Auth-Dropped-Requests` | Requests dropped (queue full, etc.) |
| `FreeRADIUS-Total-Auth-Unknown-Types` | Unrecognized packet types |
| `FreeRADIUS-Total-Accounting-Requests` | Total accounting requests received |
| `FreeRADIUS-Total-Accounting-Responses` | Total accounting responses sent |

#### Configuration Details

| Property | Value |
|----------|-------|
| Port | UDP 18121 |
| Bind address | Localhost only (via client restriction) |
| Client secret | `adminsecret` (default, override via `freeradius_status_server_secret`) |
| Virtual server | `sites-available/status` (FreeRADIUS stock config, symlinked to `sites-enabled/`) |
| Client definition | `sites-available/status-client.conf` (included from `clients.conf`) |
| Toggle | `freeradius_status_server_enabled` (default: `true`) |

#### Security

The Status-Server is restricted to localhost queries only:
- The `status_server` client block in `status-client.conf` limits `ipaddr` to `127.0.0.1`
- The status virtual server's `listen` section binds to `127.0.0.1` only
- EC2 security groups do not expose port 18121

---

### Ansible Configuration Reference

All observability configuration is managed through the `freeradius` Ansible role.

#### Role Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `freeradius_linelog_path` | `/var/log/radius/linelog.json` | Path for structured JSON log output |
| `freeradius_status_server_enabled` | `true` | Enable/disable Status-Server and its port check |
| `freeradius_status_server_port` | `18121` | UDP port for Status-Server listener |
| `freeradius_status_server_secret` | `adminsecret` | Shared secret for Status-Server client |

#### Files Deployed

| Template | Destination | Purpose |
|----------|-------------|---------|
| `linelog.j2` | `/etc/raddb/mods-available/linelog` | linelog module config (JSON format strings) |
| `status_client.j2` | `/etc/raddb/sites-available/status-client.conf` | Localhost client for status queries |

#### Tasks (in execution order)

The following tasks run in `configure.yml` before the final `radiusd -C` syntax check:

1. **Ensure log directory exists** — creates `/var/log/radius` (owner: `radiusd`, mode: `0750`)
2. **Deploy linelog module config** — templates `linelog.j2` to `mods-available/linelog`
3. **Enable linelog module** — symlinks `mods-available/linelog` to `mods-enabled/linelog`
4. **Wire linelog into post-auth** — adds `linelog` call to `post-auth {}` section
5. **Wire linelog into post-auth reject** — adds `linelog` call to `Post-Auth-Type REJECT {}` section
6. **Wire linelog into accounting** — adds `linelog` call to `accounting {}` section
7. **Enable status_server in radiusd.conf** — sets `status_server = yes` (conditional)
8. **Enable status virtual server** — symlinks `sites-available/status` to `sites-enabled/status` (conditional)
9. **Deploy status client config** — templates `status_client.j2` (conditional)
10. **Include status client in clients.conf** — adds `$INCLUDE` directive (conditional)

All tasks notify the `restart radiusd` handler. The `radiusd -C` syntax check runs last as a safety net.

In `service.yml`, a `wait_for` task confirms the Status-Server port is listening after service start (conditional on `freeradius_status_server_enabled`).

---

### Verification Runbook

After deploying, verify observability is working via SSM session on the EC2 instance:

```bash
# 1. Confirm config syntax is valid (runs automatically as last Ansible task)
radiusd -C

# 2. Confirm Status-Server port is listening
ss -ulnp | grep 18121

# 3. Send a test authentication request
radtest testrunner run123 localhost 0 testing123

# 4. Verify structured log was written
tail -1 /var/log/radius/linelog.json | jq .
# Expected: {"timestamp":"...","type":"auth","result":"accept","user":"testrunner",...}

# 5. Send a request that will be rejected
radtest baduser wrongpass localhost 0 testing123

# 6. Verify reject was logged
tail -1 /var/log/radius/linelog.json | jq .
# Expected: {"timestamp":"...","type":"auth","result":"reject","user":"baduser",...}

# 7. Query Status-Server for aggregate counters
echo "Message-Authenticator = 0x00" | radclient -x 127.0.0.1:18121 status adminsecret
# Expected: FreeRADIUS-Total-Access-Requests = 2, Accepts = 1, Rejects = 1

# 8. Confirm linelog module is enabled
ls -la /etc/raddb/mods-enabled/linelog
# Expected: symlink to ../mods-available/linelog

# 9. Confirm status virtual server is enabled
ls -la /etc/raddb/sites-enabled/status
# Expected: symlink to ../sites-available/status
```

---

### Troubleshooting

**linelog file not created:**
- Check that `/var/log/radius/` exists and is owned by `radiusd`
- Verify the symlink: `ls -la /etc/raddb/mods-enabled/linelog`
- Check for module errors: `radiusd -X` (debug mode) and look for `linelog` in output
- Verify the module is called: search for `linelog` in `sites-available/default`

**Status-Server not responding:**
- Verify `status_server = yes` in `/etc/raddb/radiusd.conf`
- Check the symlink: `ls -la /etc/raddb/sites-enabled/status`
- Verify the client is included: `grep -r status-client /etc/raddb/clients.conf`
- Check the port: `ss -ulnp | grep 18121`
- Test with verbose output: `echo "Message-Authenticator = 0x00" | radclient -x 127.0.0.1:18121 status adminsecret`

**linelog JSON is malformed:**
- Run `jq . /var/log/radius/linelog.json` — jq will report the line number of any parse error
- Attributes with special characters (quotes, backslashes) in values can break JSON; this is a known limitation of string-based templating in `rlm_linelog`

**radiusd -C fails after changes:**
- The syntax check catches misplaced `blockinfile` insertions
- Check that `insertafter` patterns in `configure.yml` still match the FreeRADIUS version's `sites-available/default` layout
- Run `radiusd -X` for detailed error output

---

## Phase 2+

_Not yet implemented. See [OBSERVABILITY_PLAN.md](OBSERVABILITY_PLAN.md) for the roadmap covering Vector agent, Grafana Cloud shipping, health checks, alerts, and CI integration._
