import os
from app.release.service import ReleaseService
from app.release.features import feature_flags

def test_release_manifest():
    m = ReleaseService().manifest()
    assert m.version
    assert m.schema_revision

def test_schema_compatibility():
    service = ReleaseService()
    m = service.manifest()
    assert service.compatibility(m.schema_revision).compatible
    assert not service.compatibility("wrong-revision").compatible

def test_feature_override(monkeypatch):
    monkeypatch.setenv("FOODINSIGHT_FEATURE_RECOVERY_CHECKS", "false")
    assert feature_flags()["recovery_checks"] is False
