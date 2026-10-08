import os
from app.readiness.models import ReadinessCheck, ReadinessReport

class ReleaseReadiness:
    def check(self) -> ReadinessReport:
        checks = []
        db_ok = bool(os.getenv("DATABASE_URL"))
        checks.append(ReadinessCheck(
            "database_url", db_ok, "blocker",
            "DATABASE_URL configured" if db_ok else "DATABASE_URL is not configured",
        ))
        security_required = os.getenv("FOODINSIGHT_REQUIRE_API_KEY", "").lower() == "true"
        security_ok = bool(os.getenv("FOODINSIGHT_API_KEY")) or not security_required
        checks.append(ReadinessCheck(
            "api_security", security_ok, "blocker",
            "API security configuration is acceptable" if security_ok else "API key required but not configured",
        ))
        checks.append(ReadinessCheck(
            "recovery_objectives", True, "warning",
            "RPO/RTO defaults are defined; production values should be reviewed",
        ))
        checks.append(ReadinessCheck(
            "destructive_restore", False, "warning",
            "Destructive restore automation is intentionally disabled",
        ))
        blockers = [c.name for c in checks if not c.passed and c.severity == "blocker"]
        return ReadinessReport(ready=not blockers, checks=checks, blockers=blockers)

readiness = ReleaseReadiness()
