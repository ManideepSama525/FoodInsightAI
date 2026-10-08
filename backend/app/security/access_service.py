from dataclasses import dataclass
from app.security.policy import AccessContext, DataClass, PolicyDecision, policy
from app.security.audit_record import AuditRecord, make_audit_record

@dataclass(frozen=True)
class AccessResult:
    decision: PolicyDecision
    audit: AuditRecord

class AccessService:
    def authorize(self, data_class: DataClass, ctx: AccessContext, action: str, resource: str) -> AccessResult:
        decision = policy.decide(data_class, ctx)
        audit = make_audit_record(
            actor=ctx.actor,
            action=action,
            resource=resource,
            decision="allow" if decision.allowed else "deny",
            reason=decision.reason,
        )
        return AccessResult(decision=decision, audit=audit)

    def authorize_export(self, ctx: AccessContext, resource: str) -> AccessResult:
        allowed = policy.can_export(ctx)
        reason = "export_policy_satisfied" if allowed else "consent_and_purpose_required"
        decision = PolicyDecision(allowed, reason, DataClass.SENSITIVE)
        audit = make_audit_record(ctx.actor, "export", resource, "allow" if allowed else "deny", reason)
        return AccessResult(decision, audit)

access_service = AccessService()
