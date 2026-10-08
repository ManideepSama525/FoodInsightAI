from app.evaluation.metrics import (
    citation_coverage,
    constraint_satisfaction,
    recall_at_k,
    token_overlap,
)
from app.evaluation.models import EvalCase, EvalMetric, EvalReport, EvalResult

class EvaluationRunner:
    def run(self, cases: list[EvalCase]) -> EvalReport:
        results=[]
        for case in cases:
            expected=case.expected
            actual=case.inputs.get("actual", {})
            metrics=[]

            if "retrieved_ids" in actual:
                value=recall_at_k(
                    expected.get("relevant_ids", []),
                    actual["retrieved_ids"],
                    expected.get("k", 5),
                )
                metrics.append(EvalMetric(name="recall_at_k", value=value))

            if "answer" in actual and "expected_answer" in expected:
                value=token_overlap(actual["answer"], expected["expected_answer"])
                metrics.append(EvalMetric(name="answer_token_overlap", value=value))

            if "cited_ids" in actual:
                value=citation_coverage(
                    actual["cited_ids"],
                    expected.get("required_citations", []),
                )
                metrics.append(EvalMetric(name="citation_coverage", value=value))

            if "violations" in actual:
                value=constraint_satisfaction(actual["violations"])
                metrics.append(EvalMetric(name="constraint_satisfaction", value=value))

            passed=all(metric.value >= expected.get("minimum_metric", 0.8) for metric in metrics)
            results.append(EvalResult(
                case_id=case.case_id,
                category=case.category,
                passed=passed,
                metrics=metrics,
                notes=case.inputs.get("notes", []),
            ))

        passed=sum(1 for r in results if r.passed)
        return EvalReport(
            total_cases=len(results),
            passed_cases=passed,
            pass_rate=(passed/len(results)) if results else 1.0,
            metrics=self._aggregate(results),
            results=results,
        )

    def _aggregate(self, results):
        names={}
        for result in results:
            for metric in result.metrics:
                names.setdefault(metric.name, []).append(metric.value)
        from app.evaluation.models import EvalMetric
        return [
            EvalMetric(name=name, value=sum(values)/len(values), details={"count":len(values)})
            for name, values in sorted(names.items())
        ]
