from app.models.entities import EvaluationRunRecord
from app.evaluation.models import EvalReport

async def persist_report(session, report: EvalReport) -> EvaluationRunRecord:
    record = EvaluationRunRecord(
        total_cases=report.total_cases,
        passed_cases=report.passed_cases,
        pass_rate=report.pass_rate,
        metrics_json=[m.model_dump() for m in report.metrics],
        results_json=[r.model_dump() for r in report.results],
    )
    session.add(record)
    await session.flush()
    return record
