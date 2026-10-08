# Phase 29 — Release Management & Provenance

Phase 29 introduces explicit release identity and compatibility checks.

## Added

- release manifest
- application version
- git/deployment reference
- schema revision tracking
- application/schema compatibility endpoint
- environment-controlled feature flags
- frontend deployment provenance panel
- release tests

## Purpose

Operational readiness now has a stable release identity that can be attached to incidents,
metrics, deployment records, and support diagnostics.

Feature flags are deliberately simple environment-controlled switches; a distributed feature
flag service can replace them later without changing the API contract.
