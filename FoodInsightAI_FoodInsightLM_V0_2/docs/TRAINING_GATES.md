# FoodInsight-LM Training Gates

## Gate 0 — Data
- [ ] USDA provenance recorded
- [ ] dataset license manifest recorded
- [ ] exact source hashes recorded
- [ ] duplicate questions removed
- [ ] food-level train/validation/test isolation verified
- [ ] final test set locked

## Gate 1 — Training
- [ ] base model hash/revision recorded
- [ ] GPU recorded
- [ ] seed recorded
- [ ] training config saved
- [ ] checkpoint saved
- [ ] tokenizer saved
- [ ] adapter config saved

## Gate 2 — Evaluation
- [ ] held-out food-level test
- [ ] numerical accuracy
- [ ] factual correctness
- [ ] evidence support
- [ ] unsupported claim rate
- [ ] uncertainty handling
- [ ] adversarial verification
- [ ] latency / VRAM

## Gate 3 — Integration
- [ ] local model provider loads adapter
- [ ] Hybrid-RAG retrieves evidence
- [ ] evidence fusion works
- [ ] ClaimVerifier runs
- [ ] feedback loop works
- [ ] citations/provenance returned

## Gate 4 — Deployment
- [ ] clean-machine load test
- [ ] no training dependency required for inference
- [ ] model artifact reproducible
- [ ] licenses documented
- [ ] rollback artifact retained
