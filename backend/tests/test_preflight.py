from app.preflight.service import ProductionPreflight
def test_production_preflight_requires_security(monkeypatch):
    monkeypatch.setenv("FOODINSIGHT_ENV","production")
    monkeypatch.setenv("DATABASE_URL","postgresql://smoke")
    monkeypatch.delenv("FOODINSIGHT_SECRET_KEY",raising=False)
    monkeypatch.delenv("FOODINSIGHT_CORS_ORIGINS",raising=False)
    monkeypatch.delenv("FOODINSIGHT_REQUIRE_API_KEY",raising=False)
    r=ProductionPreflight().run()
    assert not r.ready
    assert "secret_key" in r.blockers and "cors_origins" in r.blockers
