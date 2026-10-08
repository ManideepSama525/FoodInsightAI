import asyncio
from pathlib import Path
from PIL import Image

from app.vision.service import VisionService
from app.vision.providers import MockVisionProvider

def test_mock_vision_is_uncertain(tmp_path: Path):
    image_path = tmp_path / "food.png"
    Image.new("RGB", (100, 100), "white").save(image_path)
    result = asyncio.run(VisionService(MockVisionProvider()).analyze(str(image_path)))
    assert result.observation.confidence == 0.0
    assert result.observation.uncertainty
    assert "vision_provider_is_mock" in result.observation.warnings
