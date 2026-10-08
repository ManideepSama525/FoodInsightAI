import os

DEFAULTS = {
    "advanced_reasoning": True,
    "multimodal_workspace": True,
    "governance_gate": True,
    "recovery_checks": True,
}

def feature_flags() -> dict[str, bool]:
    result = dict(DEFAULTS)
    for name in DEFAULTS:
        raw = os.getenv(f"FOODINSIGHT_FEATURE_{name.upper()}")
        if raw is not None:
            result[name] = raw.lower() in {"1", "true", "yes", "on"}
    return result
