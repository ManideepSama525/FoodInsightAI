import os
from app.readiness.service import ReleaseReadiness

def test_release_readiness_without_db_is_blocked(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    report = ReleaseReadiness().check()
    assert not report.ready
    assert "database_url" in report.blockers

def test_release_readiness_with_db_can_pass(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://example")
    monkeypatch.delenv("FOODINSIGHT_REQUIRE_API_KEY", raising=False)
    report = ReleaseReadiness().check()
    assert report.ready
