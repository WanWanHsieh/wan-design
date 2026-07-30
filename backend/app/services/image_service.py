import io

from PIL import Image, ImageOps

MAX_DIMENSION = 2000
THUMBNAIL_SIZE = (400, 400)


def process_upload(contents: bytes) -> tuple[bytes, bytes, str]:
    """Returns (resized_original_bytes, thumbnail_bytes, format_extension)."""
    image = Image.open(io.BytesIO(contents))
    image = ImageOps.exif_transpose(image)  # respect camera orientation before resizing
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGB")

    output_format = "JPEG" if image.mode == "RGB" else "PNG"
    extension = ".jpg" if output_format == "JPEG" else ".png"
    save_kwargs = {"quality": 85, "optimize": True} if output_format == "JPEG" else {"optimize": True}

    resized = image.copy()
    resized.thumbnail((MAX_DIMENSION, MAX_DIMENSION))
    original_buffer = io.BytesIO()
    resized.save(original_buffer, format=output_format, **save_kwargs)

    thumbnail = ImageOps.fit(image, THUMBNAIL_SIZE, method=Image.LANCZOS)
    thumbnail_buffer = io.BytesIO()
    thumbnail.save(thumbnail_buffer, format=output_format, **save_kwargs)

    return original_buffer.getvalue(), thumbnail_buffer.getvalue(), extension
