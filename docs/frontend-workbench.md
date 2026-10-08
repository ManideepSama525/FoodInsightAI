# Phase 14 — Frontend Intelligence Workbench

The Next.js frontend now provides a compact operational workbench over the existing backend APIs.

## Workbench panels

- Grounded Chat
- Nutrition
- Recipe Planner
- Safety Evidence
- Knowledge Graph
- Evaluation

The UI deliberately presents structured backend results rather than recreating domain logic in the
browser.

## API configuration

Set:

`NEXT_PUBLIC_API_BASE=http://localhost:8000/api/v1`

in the frontend environment.

## Current scope

This phase establishes the frontend integration shell. Future iterations can add:
- document upload/drop zones
- image upload and visual observation
- citation/source cards
- graph visualization
- nutrition tables and charts
- recipe editing
- authentication state
- streaming chat
- evaluation dashboards
