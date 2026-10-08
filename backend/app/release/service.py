import os
from app.release.models import ReleaseManifest, CompatibilityResult, utc_now

class ReleaseService:
    def manifest(self) -> ReleaseManifest:
        return ReleaseManifest(
            version=os.getenv("FOODINSIGHT_VERSION", "0.29.0"),
            generated_at=utc_now(),
            git_ref=os.getenv("FOODINSIGHT_GIT_REF", "local"),
            schema_revision=os.getenv("FOODINSIGHT_SCHEMA_REVISION", "0003"),
            features={
                "observability": True,
                "governance": True,
                "recovery": True,
                "release_gates": True,
            },
        )

    def compatibility(self, current_schema_revision: str | None = None) -> CompatibilityResult:
        m = self.manifest()
        current = current_schema_revision or os.getenv("FOODINSIGHT_SCHEMA_REVISION", "0003")
        ok = current == m.schema_revision
        return CompatibilityResult(
            compatible=ok,
            application_version=m.version,
            required_schema_revision=m.schema_revision,
            current_schema_revision=current,
            reason="schema_revision_match" if ok else "schema_revision_mismatch",
        )

release_service = ReleaseService()
