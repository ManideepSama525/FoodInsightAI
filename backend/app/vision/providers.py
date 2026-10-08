from typing import Protocol
from pathlib import Path
from PIL import Image
from app.vision.models import FoodObservation, VisionResult

class VisionProvider(Protocol):
    model_name: str
    async def analyze(self, image_path: str, question: str | None = None) -> VisionResult:
        ...

class MockVisionProvider:
    model_name = "mock-vision-v1"

    async def analyze(self, image_path: str, question: str | None = None) -> VisionResult:
        # Conservative offline fallback: image metadata is not treated as food identity.
        try:
            with Image.open(image_path) as image:
                width, height = image.size
                fmt = image.format or "unknown"
        except Exception as exc:
            raise ValueError(f"Unable to decode image: {exc}") from exc

        return VisionResult(
            model=self.model_name,
            observation=FoodObservation(
                food_name=None,
                visible_ingredients=[],
                preparation_characteristics=[],
                visual_observations=[
                    f"Image decoded successfully ({fmt}, {width}x{height})."
                ],
                confidence=0.0,
                uncertainty=[
                    "No food identity was inferred by the local fallback provider.",
                    "Exact ingredients and nutritional values cannot be established from this fallback."
                ],
                warnings=["vision_provider_is_mock"],
            ),
        )
