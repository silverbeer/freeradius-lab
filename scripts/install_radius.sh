#!/usr/bin/env bash
#
# install_radius.sh — Download and install FreeRADIUS RPMs from S3
#
# Usage: install_radius.sh <bucket> <arch>
# Runs on the EC2 instance via SSM send-command.
#
set -euo pipefail

BUCKET="${1:?Usage: install_radius.sh <bucket> <arch>}"
ARCH="${2:?Usage: install_radius.sh <bucket> <arch>}"

echo "=== Installing FreeRADIUS from s3://${BUCKET}/rpms/${ARCH}/ ==="
echo "Timestamp: $(date -u)"

mkdir -p /tmp/rpms
aws s3 cp "s3://${BUCKET}/rpms/${ARCH}/" /tmp/rpms/ --recursive
echo "Downloaded RPMs:"
ls -lh /tmp/rpms/

echo "=== Installing RPMs ==="
dnf install -y \
    /tmp/rpms/freeradius-3.2*.rpm \
    /tmp/rpms/freeradius-config-3*.rpm \
    /tmp/rpms/freeradius-utils-3*.rpm \
    /tmp/rpms/freeradius-sqlite-3*.rpm

echo "=== Verifying installation ==="
radiusd -v
rpm -q freeradius freeradius-config freeradius-utils freeradius-sqlite

echo "=== Installation complete ==="
