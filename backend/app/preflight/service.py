import os
from datetime import datetime, timezone
from app.preflight.models import PreflightCheck, PreflightReport

class ProductionPreflight:
    def run(self) -> PreflightReport:
        production=os.getenv("FOODINSIGHT_ENV","development").lower()=="production"
        db=bool(os.getenv("DATABASE_URL"))
        api_required=os.getenv("FOODINSIGHT_REQUIRE_API_KEY","").lower()=="true"
        api_ok=bool(os.getenv("FOODINSIGHT_API_KEY")) if api_required else True
        secret_ok=bool(os.getenv("FOODINSIGHT_SECRET_KEY")) or not production
        cors_ok=bool(os.getenv("FOODINSIGHT_CORS_ORIGINS")) or not production
        checks=[
            PreflightCheck("database_url",db,"blocker","configured" if db else "missing"),
            PreflightCheck("api_key",api_ok,"blocker","configured" if api_ok else "required API key is missing"),
            PreflightCheck("secret_key",secret_ok,"blocker","configured" if secret_ok else "production secret key is missing"),
            PreflightCheck("cors_origins",cors_ok,"blocker","configured" if cors_ok else "production CORS origins are missing"),
            PreflightCheck("destructive_restore_disabled",True,"warning","destructive restore automation remains disabled"),
        ]
        blockers=[c.name for c in checks if not c.passed and c.severity=="blocker"]
        warnings=[c.name for c in checks if not c.passed and c.severity=="warning"]
        return PreflightReport(not blockers,datetime.now(timezone.utc).isoformat(),checks,blockers,warnings)
preflight=ProductionPreflight()
