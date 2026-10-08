from pathlib import Path

from PIL import Image, ImageOps

ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
MAX_PIXELS = 20_000_000


def validate_and_prepare(
    image_path,
    output_dir="/app/data/processed/images",
):
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    source = Path(image_path)

    with Image.open(source) as image:
        if image.format not in ALLOWED_FORMATS:
            raise ValueError(
                f"Unsupported image format: {image.format}"
            )

        if image.width * image.height > MAX_PIXELS:
            raise ValueError(
                f"Image exceeds maximum pixel count: "
                f"{image.width}x{image.height}"
            )

        image = ImageOps.exif_transpose(image).convert("RGB")
        image.thumbnail((2048, 2048))

        target = target_dir / f"{source.stem}_normalized.jpg"

        image.save(
            target,
            format="JPEG",
            quality=95,
            optimize=True,
        )

    return str(target)
