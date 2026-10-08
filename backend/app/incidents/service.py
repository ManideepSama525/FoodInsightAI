from datetime import datetime, timezone
from app.observability.metrics import metrics
from app.observability.sre import evaluate
from app.readiness.service import readiness
from app.release.service import release_service
from app.recovery.service import recovery_service
from app.incidents.models import IncidentReport, IncidentSignal

class IncidentCenter:
    def report(self) -> IncidentReport:
        sre = evaluate(metrics.snapshot())
        release = release_service.compatibility()
        ready = readiness.check()
        recovery = recovery_service.readiness()
        healthy = sre.get("healthy", True)
        signals = [
            IncidentSignal("sre", "healthy" if healthy else "attention",
                            "SRE thresholds within limits" if healthy else "SRE threshold violation detected"),
            IncidentSignal("release", "compatible" if release.compatible else "incompatible", release.reason),
            IncidentSignal("readiness", "ready" if ready.ready else "blocked",
                            "Release blockers: " + ", ".join(ready.blockers) if ready.blockers else "No release blockers"),
            IncidentSignal("recovery", "configured",
                            f"RPO={recovery['rpo_minutes']}m, RTO={recovery['rto_minutes']}m"),
        ]
        attention = any(x.status in {"attention", "incompatible", "blocked"} for x in signals)
        actions = []
        if not healthy: actions.append("Inspect latency/error-rate metrics and active traces.")
        if not release.compatible: actions.append("Align application and database schema revisions before deployment.")
        if not ready.ready: actions.append("Resolve release blockers before production rollout.")
        if not actions: actions.append("Continue routine monitoring; no immediate incident action is indicated.")
        return IncidentReport(datetime.now(timezone.utc).isoformat(),
                              "warning" if attention else "normal",
                              "attention" if attention else "nominal",
                              signals, actions)

incident_center = IncidentCenter()
