from pathlib import Path
import ast, json, hashlib, sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
errors = []
py_files = list((ROOT / "backend").rglob("*.py"))
for path in py_files:
    try:
        ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        errors.append({"file": str(path.relative_to(ROOT)), "error": str(exc)})

checks = {
    "python_syntax": not errors,
    "ci_workflow": (ROOT / ".github/workflows/ci.yml").exists(),
    "release_manifest": (ROOT / "backend/app/release/service.py").exists(),
    "readiness_gate": (ROOT / "backend/app/readiness/service.py").exists(),
    "recovery_layer": (ROOT / "backend/app/recovery/service.py").exists(),
}

report = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "checks": checks,
    "python_files": len(py_files),
    "syntax_errors": errors,
    "passed": all(checks.values()) and not errors,
}
out = ROOT / "artifacts"
out.mkdir(exist_ok=True)
(out / "release-validation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
sys.exit(0 if report["passed"] else 1)
