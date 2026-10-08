from app.safety.models import AdulterationSignal
from app.safety.service import SafetyService

def test_missing_evidence_is_explicitly_uncertain():
    result = SafetyService().assess("demo food", ["hazard"], ["control"])
    assert result.status == "evidence_review_required"
    assert result.uncertainty

def test_adulteration_signal_is_not_called_fraud_without_evidence():
    signal = AdulterationSignal(
        signal_id="s1",
        subject="demo food",
        indicator="unexpected marker",
        observed_value="present",
        status="observed",
    )
    result = SafetyService().evaluate_adulteration(signal)
    assert result.status == "unverified_signal"
