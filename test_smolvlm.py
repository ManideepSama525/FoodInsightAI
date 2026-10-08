import torch
from PIL import Image
from transformers import AutoProcessor, SmolVLMForConditionalGeneration

MODEL = "HuggingFaceTB/SmolVLM-500M-Instruct"
IMAGE = r"C:\Users\manid\Downloads\FoodTest.jpeg"

print("Model:", MODEL)
print("CUDA:", torch.cuda.is_available())
print("GPU:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "NONE")

image = Image.open(IMAGE).convert("RGB")
print("Image:", IMAGE)
print("Image size:", image.size)

print("\nLoading processor...")
processor = AutoProcessor.from_pretrained(MODEL)

print("Loading SmolVLM...")
model = SmolVLMForConditionalGeneration.from_pretrained(
    MODEL,
    torch_dtype=torch.float16,
    device_map="auto",
)

model.eval()

messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "image",
            },
            {
                "type": "text",
                "text": (
                    "Analyze this image carefully. "
                    "Identify the most likely food or dish. "
                    "List only ingredients that are visibly identifiable. "
                    "Do not invent ingredients. "
                    "If the food identity is uncertain, say so. "
                    "Return a concise answer."
                ),
            },
        ],
    }
]

print("\nPreparing input...")
prompt = processor.apply_chat_template(
    messages,
    add_generation_prompt=True,
)

inputs = processor(
    text=prompt,
    images=[image],
    return_tensors="pt",
)

# Move tensors to the model's device.
inputs = {
    key: value.to(model.device) if hasattr(value, "to") else value
    for key, value in inputs.items()
}

print("Generating...")
with torch.inference_mode():
    output = model.generate(
        **inputs,
        max_new_tokens=120,
        do_sample=False,
    )

input_length = inputs["input_ids"].shape[-1]
generated = output[:, input_length:]

answer = processor.batch_decode(
    generated,
    skip_special_tokens=True,
)[0].strip()

print("\n========================================")
print("VISION MODEL RESULT")
print("========================================")
print(answer)
print("========================================")

if torch.cuda.is_available():
    print(
        "\nGPU memory allocated:",
        round(torch.cuda.memory_allocated() / 1024**3, 2),
        "GB",
    )
    print(
        "GPU memory reserved:",
        round(torch.cuda.memory_reserved() / 1024**3, 2),
        "GB",
    )
