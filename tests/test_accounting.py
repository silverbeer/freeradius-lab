"""Accounting tests for FreeRADIUS (Accounting-Request → Accounting-Response)."""

import uuid

import pytest
import pyrad.packet


@pytest.fixture()
def session_id():
    """Generate a unique RADIUS session ID per test."""
    return uuid.uuid4().hex[:16]


def _create_acct_packet(radius_client, session_id, status_type, **extra):
    """Build an Accounting-Request with required AVPs."""
    req = radius_client.CreateAcctPacket(
        code=pyrad.packet.AccountingRequest,
    )
    req["User-Name"] = "testrunner"
    req["Acct-Session-Id"] = session_id
    req["Acct-Status-Type"] = status_type
    req["NAS-Identifier"] = "integration-test"
    req["NAS-IP-Address"] = "127.0.0.1"
    for key, value in extra.items():
        req[key] = value
    return req


class TestAccounting:
    """Accounting protocol tests — verify server accepts Start/Stop/Interim."""

    def test_accounting_start_accepted(self, radius_client, session_id):
        req = _create_acct_packet(radius_client, session_id, "Start")
        reply = radius_client.SendPacket(req)
        assert reply.code == pyrad.packet.AccountingResponse

    def test_accounting_stop_accepted(self, radius_client, session_id):
        # Send Start first
        start = _create_acct_packet(radius_client, session_id, "Start")
        radius_client.SendPacket(start)

        # Then Stop with session time
        stop = _create_acct_packet(
            radius_client,
            session_id,
            "Stop",
            **{"Acct-Session-Time": 120},
        )
        reply = radius_client.SendPacket(stop)
        assert reply.code == pyrad.packet.AccountingResponse

    def test_interim_update_accepted(self, radius_client, session_id):
        # Send Start first
        start = _create_acct_packet(radius_client, session_id, "Start")
        radius_client.SendPacket(start)

        # Then Interim-Update
        interim = _create_acct_packet(
            radius_client,
            session_id,
            "Interim-Update",
            **{"Acct-Session-Time": 60},
        )
        reply = radius_client.SendPacket(interim)
        assert reply.code == pyrad.packet.AccountingResponse
