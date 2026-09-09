"""
Image enhancement service — Gate 4.

Improves marketplace presentation for artisan product photos by adjusting
brightness, contrast, and sharpness using Pillow, per 04_GATE_IMAGE_ENHANCEMENT.md.

Rules:
- Do not change product color dramatically.
- Do not add artificial product features.
- Do not distort dimensions.
- Do not over-sharpen.
- Preserve alpha channel / transparency for background-removed images (from Gate 3).
"""

from io import BytesIO
from PIL import Image, ImageEnhance

# Enhancement factors specified in 04_GATE_IMAGE_ENHANCEMENT.md
BRIGHTNESS_FACTOR = 1.05  # +5%
CONTRAST_FACTOR = 1.10    # +10%
SHARPNESS_FACTOR = 1.15   # +15%


def enhance_image(data: bytes) -> bytes:
    """
    Enhance a product image's brightness, contrast, and sharpness.

    Args:
        data: raw bytes of the image (already validated by validate_image()
            or produced by remove_background()).

    Returns:
        PNG-encoded bytes of the enhanced image in RGBA mode.

    Raises:
        ValueError: if the input data cannot be decoded as an image.
    """
    if not data:
        raise ValueError("Image data is empty")

    try:
        image = Image.open(BytesIO(data))
        # Support both standard RGB images and RGBA images with transparency
        image = image.convert("RGBA")
    except Exception as exc:
        raise ValueError(f"Cannot decode image for enhancement: {exc}") from exc

    # Apply Pillow enhancements
    image = ImageEnhance.Brightness(image).enhance(BRIGHTNESS_FACTOR)
    image = ImageEnhance.Contrast(image).enhance(CONTRAST_FACTOR)
    image = ImageEnhance.Sharpness(image).enhance(SHARPNESS_FACTOR)

    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()
