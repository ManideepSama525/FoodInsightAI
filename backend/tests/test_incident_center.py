from app.incidents.service import IncidentCenter

def test_incident_report_shape(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://smoke")
    data = IncidentCenter().report().as_dict()
    assert data["status"] in {"nominal", "attention"}
    assert data["severity"] in {"normal", "warning"}
    assert len(data["signals"]) >= 4
    assert data["recommended_actions"]
