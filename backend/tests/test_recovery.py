from app.recovery.service import RecoveryService

def test_backup_manifest_and_restore_verification():
    service = RecoveryService()
    manifest = service.create_manifest("b1", "test", b"foodinsight")
    result = service.verify_restore(manifest, b"foodinsight")
    assert result.passed
    assert result.checks["checksum"]

def test_recovery_readiness():
    data = RecoveryService().readiness()
    assert data["rpo_minutes"] > 0
    assert data["rto_minutes"] > 0
    assert data["automated_destructive_restore"] is False
