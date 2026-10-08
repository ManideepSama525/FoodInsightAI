# Phase 22 — Observability & SRE

Phase 22 adds operational visibility across HTTP requests, background jobs, latency and SRE thresholds.

## Observability

- structured request logs
- request correlation IDs
- HTTP request counters
- status-code counters
- request latency measurements
- job lifecycle counters
- span-style timing utility
- `/api/v1/system/observability`

## SRE signals

The runtime evaluates:
- request latency p95
- error-rate percentage
- configurable thresholds

Threshold violations are returned as structured diagnostics rather than hidden alerts.

Production telemetry can later export these metrics to Prometheus/OpenTelemetry or an equivalent monitoring platform.
