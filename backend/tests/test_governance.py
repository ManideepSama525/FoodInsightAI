from datetime import datetime, timedelta, timezone
from app.security.policy import AccessContext, DataClass, policy
from app.security.retention import RetentionItem, retention_planner

def test_sensitive_requires_consent():
    d = policy.decide(DataClass.SENSITIVE, AccessContext("u", "analysis"))
    assert not d.allowed
    d = policy.decide(DataClass.SENSITIVE, AccessContext("u", "analysis", consent_granted=True))
    assert d.allowed

def test_admin_can_access_restricted():
    d = policy.decide(DataClass.RESTRICTED, AccessContext("admin", "ops", admin=True))
    assert d.allowed

def test_retention_planner():
    old = datetime.now(timezone.utc) - timedelta(days=100)
    plan = retention_planner.plan([RetentionItem("x", old, 90)])
    assert plan[0]["action"] == "delete"
