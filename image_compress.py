from pathlib import Path
from PIL import Image

input_path = Path(
    input("Path to the source image: ").strip().strip('"')
)

output_path = Path("tiny_image.jpg")

with Image.open(input_path) as original_image:
    image = original_image.convert("RGB")

    image.thumbnail((64, 64))

    image.save(
        output_path,
        format="JPEG",
        quality=40,
        optimize=True
    )

print("Created:", output_path)
print("Image size:", output_path.stat().st_size, "bytes")