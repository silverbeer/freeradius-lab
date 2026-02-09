# RADIUS / AAA Notes

Personal reference notes from building the FreeRADIUS lab.

## Core Concepts

_To be filled in during Phase 0..._

## FreeRADIUS Architecture

_To be filled in during Phase 0..._

## Useful Commands

```bash
# Start FreeRADIUS in debug mode (foreground, verbose output)
radiusd -X

# Test authentication
radtest <user> <password> <server> <nas-port> <secret>
radtest testuser testpass localhost 0 testing123

# Send accounting packet
echo "Acct-Status-Type = Start, User-Name = runner1, Acct-Session-Id = run-001" | \
  radclient localhost:1813 acct testing123

# Check FreeRADIUS version
radiusd -v

# Verify config syntax
radiusd -C
```

## Gotchas & Lessons Learned

_To be updated as I work through the phases..._



## Running FreeRADIUS in Docker
Terminal 1 — start FreeRADIUS in debug mode:
docker run --rm -it --name freeradius freeradius/freeradius-server -X

Terminal 2 — add the user and reload without restarting:
  docker exec freeradius sh -c 'echo '\''testuser Cleartext-Password := "testpass"'\'' >> /etc/raddb/mods-config/files/authorize'

  Tell FreeRADIUS to reload its configuration:
  docker exec freeradius kill -HUP 1

Terminal 3 — test authentication: 
  docker exec freeradius radtest testuser testpass localhost 0 testing123

## Useful notes about running FreeRADIUS locally in Docker:
       
  - The processing pipeline — what you saw: authorize {} runs first (modules vote on who the user is), then authenticate {} does the
  credential check. The pap module's warning about "no known good password" is what happens when no module in authorize claims the user.
  - Module return codes — noop means "not my problem," ok means "I handled it," notfound means "I looked but found nothing." These drive
   the pipeline flow.
  - := operator — assignment in the users file. Different from == (check) and = (set as default if not already set).
  - Container ephemeral filesystem — changes inside the container don't survive restarts. Volume mounts or rebuilding the image are the
  answers.
  - -X debug mode — indispensable for understanding what FreeRADIUS is doing. You'll use this constantly.
  - BlastRADIUS / Message-Authenticator — what it is and why the warning appears.
  - Config file hierarchy — radiusd.conf → clients.conf, mods-enabled/*, sites-enabled/*, mods-config/files/authorize