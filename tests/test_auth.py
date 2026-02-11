"""Authentication tests for FreeRADIUS (Access-Request → Accept/Reject)."""

import pyrad.packet


class TestValidAuthentication:
    """Tests for valid credentials — expect Access-Accept."""

    def test_valid_user_authenticates(self, radius_client):
        req = radius_client.CreateAuthPacket(
            code=pyrad.packet.AccessRequest,
            User_Name="testrunner",
            NAS_Identifier="integration-test",
        )
        req["User-Password"] = req.PwCrypt("run123")
        reply = radius_client.SendPacket(req)
        assert reply.code == pyrad.packet.AccessAccept

    def test_valid_user_gets_reply_message(self, radius_client):
        req = radius_client.CreateAuthPacket(
            code=pyrad.packet.AccessRequest,
            User_Name="testrunner",
            NAS_Identifier="integration-test",
        )
        req["User-Password"] = req.PwCrypt("run123")
        reply = radius_client.SendPacket(req)
        assert reply["Reply-Message"] == ["Welcome, runner!"]

    def test_valid_user_gets_session_timeout(self, radius_client):
        req = radius_client.CreateAuthPacket(
            code=pyrad.packet.AccessRequest,
            User_Name="testrunner",
            NAS_Identifier="integration-test",
        )
        req["User-Password"] = req.PwCrypt("run123")
        reply = radius_client.SendPacket(req)
        assert reply["Session-Timeout"] == [3600]


class TestInvalidAuthentication:
    """Tests for invalid credentials — expect Access-Reject."""

    def test_wrong_password_rejected(self, radius_client):
        req = radius_client.CreateAuthPacket(
            code=pyrad.packet.AccessRequest,
            User_Name="testrunner",
            NAS_Identifier="integration-test",
        )
        req["User-Password"] = req.PwCrypt("wrongpassword")
        reply = radius_client.SendPacket(req)
        assert reply.code == pyrad.packet.AccessReject

    def test_unknown_user_rejected(self, radius_client):
        req = radius_client.CreateAuthPacket(
            code=pyrad.packet.AccessRequest,
            User_Name="nonexistent_user",
            NAS_Identifier="integration-test",
        )
        req["User-Password"] = req.PwCrypt("anypassword")
        reply = radius_client.SendPacket(req)
        assert reply.code == pyrad.packet.AccessReject

    def test_empty_password_rejected(self, radius_client):
        req = radius_client.CreateAuthPacket(
            code=pyrad.packet.AccessRequest,
            User_Name="testrunner",
            NAS_Identifier="integration-test",
        )
        req["User-Password"] = req.PwCrypt("")
        reply = radius_client.SendPacket(req)
        assert reply.code == pyrad.packet.AccessReject
