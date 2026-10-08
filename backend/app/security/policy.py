from dataclasses import dataclass
from enum import Enum

class DataClass(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    SENSITIVE = "sensitive"
    RESTRICTED = "restricted"

@dataclass(frozen=True)
class AccessContext:
    actor: str
    purpose: str
    consent_granted: bool = False
    admin: bool = False

@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str
    data_class: DataClass

class GovernancePolicy:
    def decide(self, data_class: DataClass, ctx: AccessContext) -> PolicyDecision:
        if ctx.admin:
            return PolicyDecision(True, "admin_policy_override", data_class)
        if data_class in {DataClass.PUBLIC, DataClass.INTERNAL}:
            return PolicyDecision(True, "standard_access", data_class)
        if data_class == DataClass.SENSITIVE and ctx.consent_granted:
            return PolicyDecision(True, "consent_present", data_class)
        return PolicyDecision(False, "explicit_consent_required", data_class)

    def can_export(self, ctx: AccessContext) -> bool:
        return ctx.admin or (ctx.consent_granted and bool(ctx.purpose.strip()))

policy = GovernancePolicy()
