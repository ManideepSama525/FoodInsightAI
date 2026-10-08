from __future__ import annotations

import json
from pathlib import Path
from urllib import request as urllib_request

from app.vision.models import VisionResult


class LocalVisionProvider:
    model_name = "SmolVLM-500M-Instruct"

    def __init__(self):
        self._url = "http://host.docker.internal:8011/analyze"
        self._docker_data_root = Path("/app/data")
        self._host_data_root = r"C:\Users\manid\fi34\data"

    def _host_image_path(self, image_path: str) -> str:
        raw = str(image_path).replace("\\", "/")

        if raw.startswith("/app/data/"):
            relative = raw[len("/app/data/"):]
        elif raw.startswith("data/"):
            relative = raw[len("data/"):]
        else:
            raise RuntimeError(
                f"Vision image path is outside the shared data volume: {image_path}"
            )

        # IMPORTANT:
        # This is a Windows host path. Do NOT use Path.exists() here,
        # because this code executes inside the Linux Docker container.
        return self._host_data_root + "\\" + relative.replace("/", "\\")

    async def analyze(
        self,
        image_path: str,
        question: str | None = None,
    ) -> VisionResult:
        host_image_path = self._host_image_path(image_path)

        payload = {
            "image_path": host_image_path,
            "question": question,
        }

        data = json.dumps(payload).encode("utf-8")

        req = urllib_request.Request(
            self._url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib_request.urlopen(req, timeout=180) as response:
                result = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise RuntimeError(
                f"Local vision server request failed: {exc}"
            ) from exc

        return VisionResult.model_validate(result["result"])
