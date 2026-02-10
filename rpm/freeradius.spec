# Simplified FreeRADIUS RPM spec for AL2023 lab environment
# Based on upstream redhat/freeradius.spec, trimmed to core + sqlite + utils

# Don't fail on devel headers, .la/.a files, and extra docs we don't package
%define _unpackaged_files_terminate_build 0

%global _prefix /usr
%global docdir %{_docdir}/freeradius-%{version}

Name:           freeradius
Version:        3.2.8
Release:        1.lab%{?dist}
Summary:        FreeRADIUS server for AAA (Authentication, Authorization, Accounting)

License:        GPLv2+
URL:            https://freeradius.org
Source0:        https://github.com/FreeRADIUS/freeradius-server/releases/download/release_3_2_8/freeradius-server-%{version}.tar.bz2

BuildRequires:  autoconf
BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  libtool
BuildRequires:  openssl-devel
BuildRequires:  libtalloc-devel
BuildRequires:  pcre2-devel
BuildRequires:  readline-devel
BuildRequires:  zlib-devel
BuildRequires:  pam-devel
BuildRequires:  gdbm-devel
BuildRequires:  libpcap-devel
BuildRequires:  libcurl-devel
BuildRequires:  net-snmp-devel
BuildRequires:  net-snmp-utils
BuildRequires:  systemd-devel
BuildRequires:  json-c-devel
BuildRequires:  sqlite-devel
BuildRequires:  perl-devel
BuildRequires:  perl(ExtUtils::Embed)
BuildRequires:  python3-devel
BuildRequires:  krb5-devel
BuildRequires:  openldap-devel
BuildRequires:  cyrus-sasl-devel
BuildRequires:  samba-devel
BuildRequires:  libwbclient-devel
BuildRequires:  postgresql-devel
BuildRequires:  hiredis-devel

Requires:       openssl
Requires:       libtalloc
Requires:       readline
Requires:       libpcap
Requires(pre):  shadow-utils
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd

%description
FreeRADIUS is an open-source RADIUS server. This package is built from
source for a lab environment targeting Amazon Linux 2023.

%package config
Summary:        FreeRADIUS default configuration files
Requires:       %{name} = %{version}-%{release}

%description config
Default configuration files for FreeRADIUS, including virtual servers,
modules, and dictionary files.

%package utils
Summary:        FreeRADIUS client utilities
Requires:       %{name} = %{version}-%{release}

%description utils
Command-line utilities: radclient, radtest, radsniff, radeapclient, radcrypt, etc.

%package sqlite
Summary:        FreeRADIUS SQLite database module
Requires:       %{name} = %{version}-%{release}
Requires:       sqlite

%description sqlite
SQLite database backend module (rlm_sql_sqlite) for FreeRADIUS.

%package postgresql
Summary:        FreeRADIUS PostgreSQL database module
Requires:       %{name} = %{version}-%{release}

%description postgresql
PostgreSQL database backend module (rlm_sql_postgresql) for FreeRADIUS.

%package rest
Summary:        FreeRADIUS REST and JSON modules
Requires:       %{name} = %{version}-%{release}

%description rest
REST API and JSON modules (rlm_rest, rlm_json) for FreeRADIUS.

%package redis
Summary:        FreeRADIUS Redis modules
Requires:       %{name} = %{version}-%{release}

%description redis
Redis modules (rlm_redis, rlm_rediswho, rlm_cache_redis) for FreeRADIUS.

%package perl
Summary:        FreeRADIUS Perl module
Requires:       %{name} = %{version}-%{release}

%description perl
Perl module (rlm_perl) for FreeRADIUS.

%package python
Summary:        FreeRADIUS Python module
Requires:       %{name} = %{version}-%{release}

%description python
Python3 module (rlm_python3) for FreeRADIUS.

%package krb5
Summary:        FreeRADIUS Kerberos module
Requires:       %{name} = %{version}-%{release}

%description krb5
Kerberos 5 module (rlm_krb5) for FreeRADIUS.

%package ldap
Summary:        FreeRADIUS LDAP module
Requires:       %{name} = %{version}-%{release}

%description ldap
LDAP module (rlm_ldap) for FreeRADIUS.

# ---------- prep ----------

%prep
%setup -q -n freeradius-server-%{version}

# ---------- build ----------

%build
%configure \
    --libdir=%{_libdir}/freeradius \
    --sysconfdir=%{_sysconfdir} \
    --disable-ltdl-install \
    --with-gnu-ld \
    --with-threads \
    --with-thread-pool \
    --with-docdir=%{docdir} \
    --with-rlm-sql_postgresql-include-dir=/usr/include/pgsql \
    --with-rlm-sql-postgresql-lib-dir=%{_libdir} \
    --with-rlm-dbm-lib-dir=%{_libdir} \
    --with-jsonc-lib-dir=%{_libdir} \
    --with-jsonc-include-dir=/usr/include/json \
    --with-winbind-include-dir=/usr/include/samba-4.0 \
    --with-winbind-lib-dir=/usr/lib64/samba \
    --with-systemd \
    --without-rlm_eap_ikev2 \
    --without-rlm_eap_tnc \
    --without-rlm_sql_iodbc \
    --without-rlm_sql_firebird \
    --without-rlm_sql_db2 \
    --without-rlm_sql_mongo \
    --without-rlm_sql_freetds \
    --without-rlm_sql_oracle \
    --without-rlm_unbound \
    --without-rlm_yubikey \
    --without-rlm_cache_memcached \
    --without-rlm_idn \
    --without-rlm_ruby \
    --without-rlm_kafka

make %{?_smp_mflags}

# ---------- install ----------

%install
rm -rf %{buildroot}
make install R=%{buildroot}

# Create systemd unit directory and install service file
install -d -m 0755 %{buildroot}%{_unitdir}
install -m 0644 redhat/radiusd.service %{buildroot}%{_unitdir}/radiusd.service

# Create log and run directories
install -d -m 0750 %{buildroot}%{_localstatedir}/log/radius
install -d -m 0750 %{buildroot}%{_localstatedir}/log/radius/radacct
install -d -m 0755 %{buildroot}%{_localstatedir}/run/radiusd

# Create tmpfiles.d entry for /run/radiusd
install -d -m 0755 %{buildroot}%{_tmpfilesdir}
echo "d /run/radiusd 0755 radiusd radiusd -" > %{buildroot}%{_tmpfilesdir}/radiusd.conf

# ---------- scriptlets ----------

%pre
getent group radiusd >/dev/null || groupadd -r radiusd
getent passwd radiusd >/dev/null || \
    useradd -r -g radiusd -d %{_localstatedir}/lib/radiusd -s /sbin/nologin \
    -c "FreeRADIUS server" radiusd
exit 0

%post
%systemd_post radiusd.service

%preun
%systemd_preun radiusd.service

%postun
%systemd_postun_with_restart radiusd.service

# ---------- files ----------

%files
%license LICENSE
%doc COPYRIGHT README.rst
%{_sbindir}/radiusd
%{_sbindir}/radmin
%{_sbindir}/checkrad
%{_sbindir}/raddebug
%{_sbindir}/rc.radiusd
%dir %{_libdir}/freeradius
%{_libdir}/freeradius/lib*.so*
# Protocol modules
%{_libdir}/freeradius/proto_*.so
# Core rlm modules (glob all, then exclude subpackage modules)
%{_libdir}/freeradius/rlm_*.so
%exclude %{_libdir}/freeradius/rlm_sql_sqlite.so
%exclude %{_libdir}/freeradius/rlm_sql_postgresql.so
%exclude %{_libdir}/freeradius/rlm_rest.so
%exclude %{_libdir}/freeradius/rlm_json.so
%exclude %{_libdir}/freeradius/rlm_redis.so
%exclude %{_libdir}/freeradius/rlm_rediswho.so
%exclude %{_libdir}/freeradius/rlm_cache_redis.so
%exclude %{_libdir}/freeradius/rlm_perl.so
%exclude %{_libdir}/freeradius/rlm_python3.so
%exclude %{_libdir}/freeradius/rlm_krb5.so
%exclude %{_libdir}/freeradius/rlm_ldap.so
%dir %{_datadir}/freeradius
%{_datadir}/freeradius/*
%{_unitdir}/radiusd.service
%{_tmpfilesdir}/radiusd.conf
%dir %attr(0750,radiusd,radiusd) %{_localstatedir}/log/radius
%dir %attr(0750,radiusd,radiusd) %{_localstatedir}/log/radius/radacct
%dir %attr(0755,radiusd,radiusd) %{_localstatedir}/run/radiusd
%{_mandir}/man5/*
%{_mandir}/man8/*

%files config
%dir %attr(0750,root,radiusd) %{_sysconfdir}/raddb
%config(noreplace) %attr(-,root,radiusd) %{_sysconfdir}/raddb/*

%files utils
%{_bindir}/radclient
%{_bindir}/radtest
%{_bindir}/radcrypt
%{_bindir}/radeapclient
%{_bindir}/radsniff
%{_bindir}/radwho
%{_bindir}/radsqlrelay
%{_bindir}/rlm_sqlippool_tool
%{_bindir}/radattr
%{_bindir}/radlast
%{_bindir}/radsecret
%{_bindir}/radzap
%{_bindir}/rad_counter
%{_bindir}/dhcpclient
%{_bindir}/map_unit
%{_bindir}/smbencrypt
%{_bindir}/rlm_ippool_tool
%{_mandir}/man1/*

%files sqlite
%{_libdir}/freeradius/rlm_sql_sqlite.so

%files postgresql
%{_libdir}/freeradius/rlm_sql_postgresql.so

%files rest
%{_libdir}/freeradius/rlm_rest.so
%{_libdir}/freeradius/rlm_json.so

%files redis
%{_libdir}/freeradius/rlm_redis.so
%{_libdir}/freeradius/rlm_rediswho.so
%{_libdir}/freeradius/rlm_cache_redis.so

%files perl
%{_libdir}/freeradius/rlm_perl.so

%files python
%{_libdir}/freeradius/rlm_python3.so

%files krb5
%{_libdir}/freeradius/rlm_krb5.so

%files ldap
%{_libdir}/freeradius/rlm_ldap.so

%changelog
* Sun Feb 09 2025 Tom Drake <lab@freeradius-lab> - 3.2.8-1.lab
- Initial lab build of FreeRADIUS 3.2.8 for Amazon Linux 2023
- Trimmed spec: core + sqlite + postgresql + utils + rest + redis
- Disabled unavailable modules: freetds, oracle, kafka, unbound, ruby, yubikey, memcached
