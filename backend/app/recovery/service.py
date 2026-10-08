from hashlib import sha256
from pathlib import Path
from app.recovery.models import BackupManifest, BackupStatus, RecoveryObjectives, RestoreVerification, utc_now

class RecoveryService:
    def __init__(self, objectives: RecoveryObjectives | None = None):
        self.objectives = objectives or RecoveryObjectives()

    def create_manifest(self, backup_id: str, source: str, payload: bytes = b"") -> BackupManifest:
        checksum = sha256(payload).hexdigest() if payload else None
        return BackupManifest(
            backup_id=backup_id,
            created_at=utc_now(),
            source=source,
            status=BackupStatus.PLANNED,
            object_count=1 if payload else 0,
            checksum=checksum,
            size_bytes=len(payload),
        )

    def verify_restore(self, manifest: BackupManifest, restored_payload: bytes = b"") -> RestoreVerification:
        checksum_ok = bool(manifest.checksum) and sha256(restored_payload).hexdigest() == manifest.checksum
        nonempty_ok = manifest.object_count == 0 or len(restored_payload) > 0
        checks = {"checksum": checksum_ok, "restored_data_present": nonempty_ok}
        return RestoreVerification(
            backup_id=manifest.backup_id,
            verified_at=utc_now(),
            checks=checks,
            passed=all(checks.values()),
            notes="Verification is integrity-oriented; database/application replay must be validated separately.",
        )

    def readiness(self) -> dict:
        return {
            "rpo_minutes": self.objectives.rpo_minutes,
            "rto_minutes": self.objectives.rto_minutes,
            "restore_verification_supported": True,
            "automated_destructive_restore": False,
        }

recovery_service = RecoveryService()
