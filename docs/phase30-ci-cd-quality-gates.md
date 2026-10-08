# Phase 30 — CI/CD Quality Gates

Phase 30 establishes repeatable build validation and provenance artifacts.

## CI

`.github/workflows/ci.yml` validates:

- backend installation
- Python compilation
- backend tests
- frontend dependency installation
- frontend production build

## Local release validation

Run:

```bash
python scripts/validate_release.py
python scripts/build_manifest.py
```

The validation report records which structural release gates passed.
The build manifest records SHA-256 hashes for project files.

CI configuration is intentionally explicit and conservative; deployment itself remains
a separate environment-specific concern.
