# FoodInsight training dataset

The dataset is intentionally not populated with unverified web text.

Create versioned JSONL records with:
- `id`
- `source`
- `question`
- `context`
- `answer`
- `claims`
- `evidence_ids`
- `split`

Recommended splits are source-disjoint where possible:
- train
- validation
- test

Do not place secrets, private medical records, or copyrighted full-text material
into the training set without appropriate rights.
