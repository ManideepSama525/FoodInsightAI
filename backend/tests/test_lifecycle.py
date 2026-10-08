from app.security.lifecycle import mark_for_deletion, mark_for_retention

def test_lifecycle_hooks():
    assert mark_for_retention("doc-1").action == "retention_registered"
    assert mark_for_deletion("doc-1").action == "deletion_requested"
