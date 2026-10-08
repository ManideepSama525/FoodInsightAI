# Nutrition and Recipe Intelligence

## Design principle

Nutrition is treated as structured domain data rather than free-form LLM knowledge.

```text
FoodRecord
  ↓
NutritionService
  ↓
serving-size scaling
  ↓
NutritionEstimate
```

The current catalog is explicitly **synthetic demo data**. It is intended to exercise the architecture and must be replaced or augmented with a licensed/authoritative food-composition dataset before scientific or consumer deployment.

## Recipe pipeline

```text
RecipeRequest
  ↓
candidate generation
  ↓
constraint validation
  ↓
allergy/exclusion checks
  ↓
Recipe
```

The recipe schema keeps:
- ingredients
- quantities
- preparation steps
- substitutions
- constraint notes
- nutrition basis
- safety notes

An LLM can later act as a candidate generator, but structured validators remain responsible for constraints.

## No invented nutrition

Recipe generation does not automatically attach precise nutritional values. Those values should be calculated from matched food records, recipe quantities, and serving definitions.
