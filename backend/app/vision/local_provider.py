from __future__ import annotations

import asyncio

import torch
from PIL import Image
from transformers import AutoProcessor, SmolVLMForConditionalGeneration

from app.vision.models import FoodObservation, VisionResult


class LocalVisionProvider:
    model_name = "SmolVLM-500M-Instruct"
    model_id = "HuggingFaceTB/SmolVLM-500M-Instruct"

    def __init__(self):
        self._processor = None
        self._model = None
        self._load_lock = asyncio.Lock()
        self._generation_lock = asyncio.Lock()

    async def _ensure_loaded(self):
        if self._model is not None:
            return

        async with self._load_lock:
            if self._model is not None:
                return

            def load():
                processor = AutoProcessor.from_pretrained(self.model_id)

                model = SmolVLMForConditionalGeneration.from_pretrained(
                    self.model_id,
                    torch_dtype=torch.float16,
                    device_map="auto",
                )

                model.eval()
                return processor, model

            self._processor, self._model = await asyncio.to_thread(load)

    async def analyze(self, image_path: str, question: str | None = None):
        await self._ensure_loaded()

        async with self._generation_lock:

            def generate():
                with Image.open(image_path) as image:
                    image = image.convert("RGB")

                    messages = [
                        {
                            "role": "user",
                            "content": [
                                {"type": "image"},
                                {
                                    "type": "text",
                                    "text": (
                                        "What food or dish is shown in this image? "
                                        "Answer with only the food name."
                                    ),
                                },
                            ],
                        }
                    ]

                    text = self._processor.apply_chat_template(
                        messages,
                        add_generation_prompt=True,
                    )

                    inputs = self._processor(
                        text=text,
                        images=[image],
                        return_tensors="pt",
                    )

                    inputs = {
                        k: v.to(self._model.device)
                        if hasattr(v, "to")
                        else v
                        for k, v in inputs.items()
                    }

                    with torch.no_grad():
                        generated = self._model.generate(
                            **inputs,
                            max_new_tokens=32,
                            do_sample=False,
                        )

                    prompt_length = inputs["input_ids"].shape[1]

                    generated_tokens = generated[:, prompt_length:]

                    answer = self._processor.batch_decode(
                        generated_tokens,
                        skip_special_tokens=True,
                    )[0].strip()

                    return answer

            raw_answer = await asyncio.to_thread(generate)

        print("=== RAW SMOLVLM OUTPUT ===")
        print(repr(raw_answer))

        if not raw_answer:
            observation = FoodObservation(
                uncertainty=[
                    "SmolVLM returned an empty response."
                ],
                warnings=["vision_model_empty_output"],
            )
        else:
            observation = FoodObservation(
                food_name=raw_answer.strip(),
                visual_observations=[
                    "Food identity inferred from the image by SmolVLM."
                ],
                confidence=0.70,
                uncertainty=[
                    "Visual identification does not establish exact ingredients.",
                    "Nutritional values must be obtained from evidence retrieval.",
                ],
            )

        return VisionResult(
            observation=observation,
            model=self.model_name,
        )
