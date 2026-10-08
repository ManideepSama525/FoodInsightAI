from app.security.access_service import access_service
from app.security.policy import AccessContext, DataClass

def test_sensitive_access_denied_without_consent():
    r = access_service.authorize(
        DataClass.SENSITIVE,
        AccessContext("u", "analysis"),
        "read",
        "nutrition-profile",
    )
    assert not r.decision.allowed
    assert r.audit.decision == "deny"

def test_export_requires_consent_or_admin():
    denied = access_service.authorize_export(AccessContext("u", "export"))
    assert not denied.decision.allowed
    allowed = access_service.authorize_export(AccessContext("u", "export", consent_granted=True))
    assert allowed.decision.allowed
    admin = access_service.authorize_export(AccessContext("admin", "ops", admin=True))
    assert admin.decision.allowed
