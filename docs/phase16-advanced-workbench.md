# Phase 16 — Advanced Frontend UX & Visualization

The workbench now presents the major FoodInsightAI intelligence surfaces in one responsive dashboard.

## Surfaces

1. **Source intake** — file selection, local image preview, upload and source metadata.
2. **Visual evidence** — image-analysis result surface.
3. **Grounded conversation** — question/answer workflow.
4. **Nutrition lookup** — structured food search.
5. **Recipe planner** — constraint-aware recipe generation.
6. **Safety evidence** — evidence-first safety assessment.
7. **Knowledge graph** — entity resolution/context.
8. **Evaluation dashboard** — evaluation trigger and metric cards.

The frontend deliberately renders backend JSON as an auditable fallback rather than inventing a presentation schema that the API does not guarantee.

## Design principle

The interface distinguishes:
- observed information,
- structured catalog information,
- retrieved evidence,
- generated recommendations,
- evaluation measurements.

This preserves the project's evidence-first architecture while making the system easier to inspect.
