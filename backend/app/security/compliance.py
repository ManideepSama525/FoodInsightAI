from dataclasses import dataclass
import re
from typing import Any

@dataclass(frozen=True)
class CompliancePolicy:
    retention_days: int = 90
    redact_email: bool = True
    redact_phone: bool = True
    redact_api_keys: bool = True

EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE = re.compile(r"(?<!\d)(?:\+?\d[\d .()\-]{7,}\d)(?!\d)")
API_KEY = re.compile(r"(?i)\b(?:sk-|api[_-]?key[=: ]+)\S+")

def redact_text(value: str, policy: CompliancePolicy | None = None) -> str:
    policy = policy or CompliancePolicy()
    result = value
    if policy.redact_email:
        result = EMAIL.sub("[REDACTED_EMAIL]", result)
    if policy.redact_phone:
        result = PHONE.sub("[REDACTED_PHONE]", result)
    if policy.redact_api_keys:
        result = API_KEY.sub("[REDACTED_SECRET]", result)
    return result

def redact_payload(payload: Any, policy: CompliancePolicy | None = None) -> Any:
    if isinstance(payload, str):
        return redact_text(payload, policy)
    if isinstance(payload, dict):
        return {str(k): redact_payload(v, policy) for k, v in payload.items()}
    if isinstance(payload, list):
        return [redact_payload(v, policy) for v in payload]
    if isinstance(payload, tuple):
        return tuple(redact_payload(v, policy) for v in payload)
    return payload
