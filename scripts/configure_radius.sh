#!/usr/bin/env bash
#
# configure_radius.sh — Post-deploy FreeRADIUS configuration
#
# Adds test NAS clients and users, then starts the RADIUS service.
# Runs on the EC2 instance via SSM send-command.
#
set -euo pipefail

echo "=== FreeRADIUS post-deploy configuration ==="
echo "Timestamp: $(date -u)"

RADDB="/etc/raddb"

# ── 1. Configure test NAS client ─────────────────────────────────
# The default clients.conf has a localhost entry with secret "testing123".
# Add a "lab-test-client" that accepts from any IP.
# Security group rules (UDP 1812/1813) are the real access control.

if ! grep -q "lab-test-client" "${RADDB}/clients.conf"; then
    cat >> "${RADDB}/clients.conf" << 'CLIENT_EOF'

# Lab test client — accepts from any IP (security group is the perimeter)
client lab-test-client {
    ipaddr          = 0.0.0.0/0
    secret          = testing123
    shortname       = lab-test
    nastype         = other
}
CLIENT_EOF
    echo "Added lab-test-client to clients.conf"
else
    echo "lab-test-client already exists in clients.conf"
fi

# ── 2. Configure test users ──────────────────────────────────────
# FreeRADIUS 3.x uses mods-config/files/authorize for the "files" module.

AUTHORIZE_FILE="${RADDB}/mods-config/files/authorize"

if ! grep -q "testrunner" "${AUTHORIZE_FILE}"; then
    cat >> "${AUTHORIZE_FILE}" << 'USERS_EOF'

# ── Lab test users ──
testrunner  Cleartext-Password := "run123"
    Reply-Message := "Welcome, runner!",
    Session-Timeout := 3600

eliterunner Cleartext-Password := "elite456"
    Reply-Message := "Welcome, elite runner!",
    Session-Timeout := 7200,
    Framed-Protocol := PPP
USERS_EOF
    echo "Added test users to authorize file"
else
    echo "Test users already exist in authorize file"
fi

# ── 3. Verify configuration syntax ───────────────────────────────
echo "Verifying radiusd configuration..."
radiusd -C
echo "Configuration syntax OK"

# ── 4. Enable and start radiusd ──────────────────────────────────
echo "Enabling and starting radiusd..."
systemctl enable radiusd
systemctl start radiusd
sleep 2

if systemctl is-active --quiet radiusd; then
    echo "radiusd is running"
    systemctl status radiusd --no-pager
else
    echo "ERROR: radiusd failed to start"
    journalctl -u radiusd --no-pager -n 50
    exit 1
fi

echo "=== Configuration complete ==="
