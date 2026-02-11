"""Per-user authorization attribute tests for FreeRADIUS."""

import pyrad.packet


def _authenticate(radius_client, username, password):
    """Send Access-Request and return the reply packet."""
    req = radius_client.CreateAuthPacket(
        code=pyrad.packet.AccessRequest,
        User_Name=username,
        NAS_Identifier="integration-test",
    )
    req["User-Password"] = req.PwCrypt(password)
    return radius_client.SendPacket(req)


class TestTestrunnerAttributes:
    """Verify reply attributes for the testrunner user."""

    def test_testrunner_session_timeout(self, radius_client):
        reply = _authenticate(radius_client, "testrunner", "run123")
        assert reply.code == pyrad.packet.AccessAccept
        assert reply["Session-Timeout"] == [3600]

    def test_testrunner_reply_message(self, radius_client):
        reply = _authenticate(radius_client, "testrunner", "run123")
        assert reply.code == pyrad.packet.AccessAccept
        assert reply["Reply-Message"] == ["Welcome, runner!"]

    def test_testrunner_no_framed_protocol(self, radius_client):
        reply = _authenticate(radius_client, "testrunner", "run123")
        assert reply.code == pyrad.packet.AccessAccept
        assert "Framed-Protocol" not in reply


class TestEliterunnerAttributes:
    """Verify reply attributes for the eliterunner user."""

    def test_eliterunner_session_timeout(self, radius_client):
        reply = _authenticate(radius_client, "eliterunner", "elite456")
        assert reply.code == pyrad.packet.AccessAccept
        assert reply["Session-Timeout"] == [7200]

    def test_eliterunner_reply_message(self, radius_client):
        reply = _authenticate(radius_client, "eliterunner", "elite456")
        assert reply.code == pyrad.packet.AccessAccept
        assert reply["Reply-Message"] == ["Welcome, elite runner!"]

    def test_eliterunner_framed_protocol(self, radius_client):
        reply = _authenticate(radius_client, "eliterunner", "elite456")
        assert reply.code == pyrad.packet.AccessAccept
        # pyrad returns integer values resolved via dictionary VALUE entries
        # Framed-Protocol PPP = 1
        assert reply["Framed-Protocol"] == ["PPP"]
