#!/usr/bin/env bash
#
# build.sh — Build FreeRADIUS RPM on Amazon Linux 2023
#
# This script is the single source of truth for the RPM build.
# It runs directly on any AL2023 environment (Docker, GHA, or bare EC2).
#
# Usage:
#   ./rpm/build.sh                  # build with default release tag
#   ./rpm/build.sh --release abc1234  # stamp RPM release with git SHA
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SPEC_FILE="${SCRIPT_DIR}/freeradius.spec"

VERSION="3.2.8"
RELEASE_TAG=""
TARBALL_URL="https://github.com/FreeRADIUS/freeradius-server/releases/download/release_3_2_8/freeradius-server-${VERSION}.tar.bz2"

# ---------- parse args ----------

while [[ $# -gt 0 ]]; do
    case "$1" in
        --release)
            RELEASE_TAG="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
done

# ---------- install build dependencies ----------

echo "==> Installing build dependencies..."
dnf install -y \
    rpm-build \
    rpmdevtools \
    gcc \
    make \
    autoconf \
    libtool \
    openssl \
    openssl-devel \
    libtalloc-devel \
    pcre2-devel \
    readline-devel \
    zlib-devel \
    pam-devel \
    gdbm-devel \
    libpcap-devel \
    libcurl-devel \
    net-snmp-devel \
    net-snmp-utils \
    systemd-devel \
    json-c-devel \
    sqlite-devel \
    perl-devel \
    'perl(ExtUtils::Embed)' \
    python3-devel \
    krb5-devel \
    openldap-devel \
    cyrus-sasl-devel \
    samba-devel \
    libwbclient-devel \
    postgresql-devel \
    hiredis-devel \
    bzip2 \
    tar \
    wget

# ---------- set up rpmbuild tree ----------

echo "==> Setting up rpmbuild tree..."
RPMBUILD_DIR="${HOME}/rpmbuild"
rpmdev-setuptree

# ---------- download source tarball ----------

echo "==> Downloading FreeRADIUS ${VERSION} source tarball..."
if [[ ! -f "${RPMBUILD_DIR}/SOURCES/freeradius-server-${VERSION}.tar.bz2" ]]; then
    wget -q -O "${RPMBUILD_DIR}/SOURCES/freeradius-server-${VERSION}.tar.bz2" "${TARBALL_URL}"
fi
echo "    SHA256: $(sha256sum "${RPMBUILD_DIR}/SOURCES/freeradius-server-${VERSION}.tar.bz2" | cut -d' ' -f1)"

# ---------- copy spec file ----------

echo "==> Copying spec file..."
cp "${SPEC_FILE}" "${RPMBUILD_DIR}/SPECS/freeradius.spec"

# ---------- optionally override release tag ----------

if [[ -n "${RELEASE_TAG}" ]]; then
    echo "==> Stamping release with: ${RELEASE_TAG}"
    sed -i "s/^Release:.*/Release:        1.lab.${RELEASE_TAG}%{?dist}/" \
        "${RPMBUILD_DIR}/SPECS/freeradius.spec"
fi

# ---------- build ----------

echo "==> Running rpmbuild..."
rpmbuild -ba "${RPMBUILD_DIR}/SPECS/freeradius.spec"

# ---------- report results ----------

echo ""
echo "==> Build complete. RPMs:"
find "${RPMBUILD_DIR}/RPMS" -name "*.rpm" -type f | sort
echo ""
echo "==> Source RPM:"
find "${RPMBUILD_DIR}/SRPMS" -name "*.rpm" -type f | sort
