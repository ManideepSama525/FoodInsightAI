from app.core.config import settings
from app.vision.models import VisionResult
from app.vision.http_provider import LocalVisionProvider


class VisionService:
    def __init__(self, provider=None):
        self.provider = provider or self._create_provider()

    @staticmethod
    def _create_provider():
        if settings.vision_provider == "local":
            return LocalVisionProvider()

        raise RuntimeError(
            f"Unsupported VISION_PROVIDER={settings.vision_provider!r}. "
            "Supported provider: local."
        )

    async def analyze(
        self,
        image_path: str,
        question: str | None = None,
    ) -> VisionResult:
        from app.vision.preprocess import validate_and_prepare

        prepared = validate_and_prepare(image_path)
        return await self.provider.analyze(prepared, question)
