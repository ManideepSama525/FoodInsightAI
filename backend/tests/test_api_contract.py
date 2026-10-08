from app.api_contract.metadata import CONTRACT

def test_contract_metadata():
    data = CONTRACT.as_dict()
    assert data["version"] == "v1"
    assert data["status"] == "stable"
    assert "chat" in data["capabilities"]
    assert "governance" in data["capabilities"]
