from collections.abc import Sequence

def exact_match(actual: str, expected: str) -> float:
    return 1.0 if actual.strip().casefold() == expected.strip().casefold() else 0.0

def token_overlap(actual: str, expected: str) -> float:
    a=set(actual.casefold().split())
    b=set(expected.casefold().split())
    if not b:
        return 1.0
    return len(a & b) / len(b)

def recall_at_k(relevant_ids: Sequence[str], retrieved_ids: Sequence[str], k: int) -> float:
    relevant=set(relevant_ids)
    if not relevant:
        return 1.0
    return len(relevant & set(retrieved_ids[:k])) / len(relevant)

def citation_coverage(cited_ids: Sequence[str], required_ids: Sequence[str]) -> float:
    required=set(required_ids)
    if not required:
        return 1.0
    return len(required & set(cited_ids)) / len(required)

def constraint_satisfaction(violations: Sequence[str]) -> float:
    return 1.0 if not violations else 0.0
