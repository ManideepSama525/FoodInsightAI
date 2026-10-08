from dataclasses import dataclass

@dataclass
class Probe:
    name: str
    status: str
    detail: str

class ReadinessService:
    def checks(self) -> list[Probe]:
        return [
            Probe("application", "ready", "Application process is responding"),
            Probe("database", "configured", "Database dependency is configured through Async SQLAlchemy"),
            Probe("vector_store", "configured", "Vector store adapter is available"),
        ]
