from pathlib import Path
from app.acceptance.service import SystemAcceptance

def test_system_acceptance():
    report = SystemAcceptance(Path(__file__).resolve().parents[2]).run()
    assert report["passed"]
    assert len(report["checks"]) >= 8
