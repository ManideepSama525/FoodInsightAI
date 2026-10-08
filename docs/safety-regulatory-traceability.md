# Phase 7 — Safety, Evidence, Traceability and Feedback

## Evidence-first safety

Safety assessments distinguish:
- observed hazards
- proposed controls
- supporting evidence
- confidence
- jurisdiction
- effective date
- unresolved uncertainty

The API does not manufacture regulatory facts when evidence is absent.

## Adulteration

An adulteration indicator is represented as a **signal**, not a conclusion about fraud or intent. A signal without supporting evidence is explicitly marked `unverified_signal`.

## Traceability

Trace events preserve:
- subject
- event type
- actor
- timestamp
- location
- metadata

The Phase 7 in-memory implementation is a development scaffold. Production should persist immutable or append-only trace events.

## Feedback

Feedback is stored separately from authoritative evidence. User ratings and comments can inform product improvement but do not become scientific or regulatory evidence merely because they are numerous.

## API

- `POST /api/v1/safety/assess`
- `POST /api/v1/safety/adulteration`
- `POST /api/v1/traceability/events`
- `GET /api/v1/traceability/history/{subject_id}`
- `POST /api/v1/feedback`
- `GET /api/v1/feedback/{subject_id}`
