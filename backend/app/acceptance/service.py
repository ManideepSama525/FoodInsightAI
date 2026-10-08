import ast
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

@dataclass(frozen=True)
class AcceptanceCheck:
    name: str
    passed: bool
    detail: str

    def as_dict(self):
        return asdict(self)

class SystemAcceptance:
    def __init__(self, root: Path | None = None):
        self.root = root or Path(__file__).resolve().parents[3]

    def run(self):
        checks = []
        py_files = list((self.root / "backend").rglob("*.py"))
        syntax_ok = True
        for f in py_files:
            try:
                ast.parse(f.read_text(encoding="utf-8"))
            except SyntaxError:
                syntax_ok = False
                break

        checks.append(AcceptanceCheck("python_syntax", syntax_ok, f"{len(py_files)} Python files checked"))
        checks.append(AcceptanceCheck("ci_pipeline", (self.root / ".github/workflows/ci.yml").exists(), "CI workflow present"))
        checks.append(AcceptanceCheck("release_validation", (self.root / "scripts/validate_release.py").exists(), "Release validation present"))
        checks.append(AcceptanceCheck("api_contract", (self.root / "backend/app/api_contract/metadata.py").exists(), "API contract present"))
        checks.append(AcceptanceCheck("governance", (self.root / "backend/app/security/policy.py").exists(), "Governance policy present"))
        checks.append(AcceptanceCheck("recovery", (self.root / "backend/app/recovery/service.py").exists(), "Recovery service present"))
        checks.append(AcceptanceCheck("incident_center", (self.root / "backend/app/incidents/service.py").exists(), "Incident center present"))
        checks.append(AcceptanceCheck("preflight", (self.root / "backend/app/preflight/service.py").exists(), "Production preflight present"))
        checks.append(AcceptanceCheck("frontend", (self.root / "frontend/app/page.tsx").exists(), "Frontend workbench present"))

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "passed": all(c.passed for c in checks),
            "checks": [c.as_dict() for c in checks],
        }

acceptance = SystemAcceptance()
