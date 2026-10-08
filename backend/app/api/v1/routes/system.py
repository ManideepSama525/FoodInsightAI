from fastapi import APIRouter
from app.jobs.metrics import metrics
from app.observability.metrics import metrics as obs_metrics
from app.observability.sre import evaluate
from app.observability.prometheus import exposition
from app.observability.diagnostics import snapshot
from app.security.governance import governance
from app.security.policy import AccessContext, DataClass, policy
from app.security.audit_record import make_audit_record
from app.security.access_service import access_service
from app.recovery.service import recovery_service
from app.readiness.service import readiness
from app.release.service import release_service
from app.release.features import feature_flags
from app.api_contract.metadata import CONTRACT
from app.jobs.runtime import settings
from fastapi import Depends
from app.security.auth import require_api_key
from app.observability.readiness import ReadinessService

router=APIRouter()
readiness=ReadinessService()

@router.get("/live")
async def live():
    return {"status":"ok"}

@router.get("/ready")
async def ready():
    probes=readiness.checks()
    return {
        "status":"ready" if all(p.status in {"ready","configured"} for p in probes) else "not_ready",
        "checks":[p.__dict__ for p in probes],
    }

@router.get("/security")
async def security_status(_: str | None = Depends(require_api_key)):
    return {
        "authentication_required": __import__("app.security.config", fromlist=["security_settings"]).security_settings.require_api_key
    }


@router.get("/metrics")
async def metrics_snapshot():
    return {
        "jobs": metrics.snapshot(),
        "worker": {
            "concurrency": settings.concurrency,
            "queue": settings.queue_name,
            "dead_letter_queue": settings.dead_letter_queue,
        },
    }


@router.get("/observability")
async def observability():
    snapshot = obs_metrics.snapshot()
    return {
        "metrics": snapshot,
        "sre": evaluate(snapshot),
    }


@router.get("/metrics/prometheus", include_in_schema=False)
async def prometheus_metrics():
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(exposition(), media_type="text/plain; version=0.0.4")


@router.get("/diagnostics")
async def diagnostics():
    return snapshot()


@router.get("/compliance")
async def compliance_policy():
    return {
        "retention_days": governance.policy.retention_days,
        "redaction": {
            "email": governance.policy.redact_email,
            "phone": governance.policy.redact_phone,
            "api_keys": governance.policy.redact_api_keys,
        },
        "audit_payloads_redacted": True,
    }

@router.post("/data-subjects/{subject_id}/deletion-plan")
async def deletion_plan(subject_id: str):
    return governance.deletion_plan(subject_id)


@router.post("/policy/check")
async def policy_check(data_class: DataClass, actor: str, purpose: str, consent_granted: bool = False, admin: bool = False):
    ctx = AccessContext(actor=actor, purpose=purpose, consent_granted=consent_granted, admin=admin)
    decision = policy.decide(data_class, ctx)
    audit = make_audit_record(actor, "policy_check", data_class.value, "allow" if decision.allowed else "deny", decision.reason)
    return {
        "allowed": decision.allowed,
        "reason": decision.reason,
        "data_class": decision.data_class.value,
        "audit": {
            "event_id": audit.event_id,
            "timestamp": audit.timestamp.isoformat(),
            "action": audit.action,
        },
    }


@router.post("/policy/export")
async def export_policy(actor: str, purpose: str, consent_granted: bool = False, admin: bool = False):
    from app.security.policy import AccessContext
    ctx = AccessContext(actor=actor, purpose=purpose, consent_granted=consent_granted, admin=admin)
    result = access_service.authorize_export(ctx, "data-export")
    return {
        "allowed": result.decision.allowed,
        "reason": result.decision.reason,
        "audit": {
            "event_id": result.audit.event_id,
            "timestamp": result.audit.timestamp.isoformat(),
            "action": result.audit.action,
        },
    }


@router.get("/recovery")
async def recovery_status():
    return recovery_service.readiness()

@router.post("/recovery/verify")
async def recovery_verify(backup_id: str, payload: str):
    manifest = recovery_service.create_manifest(backup_id, "operator-supplied", payload.encode())
    verification = recovery_service.verify_restore(manifest, payload.encode())
    return {
        "manifest": manifest.as_dict(),
        "verification": {
            "backup_id": verification.backup_id,
            "verified_at": verification.verified_at,
            "checks": verification.checks,
            "passed": verification.passed,
            "notes": verification.notes,
        },
    }


@router.get("/release-readiness")
async def release_readiness():
    return readiness.check().as_dict()


@router.get("/release")
async def release_manifest():
    return release_service.manifest().as_dict()

@router.get("/release/compatibility")
async def release_compatibility(schema_revision: str | None = None):
    return release_service.compatibility(schema_revision).__dict__

@router.get("/features")
async def features():
    return feature_flags()


@router.get("/contract")
async def api_contract():
    return CONTRACT.as_dict()

from app.incidents.service import incident_center


@router.get("/incident-center")
async def incident_report():
    return incident_center.report().as_dict()

from app.preflight.service import preflight


@router.get("/preflight")
async def production_preflight():
    return preflight.run().as_dict()

from app.acceptance.service import acceptance


@router.get("/acceptance")
async def system_acceptance():
    return acceptance.run()
