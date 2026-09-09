"""
Image validation service — Gate 2.

Validates an uploaded product image before it is allowed into any later
AI processing stage (background removal, enhancement, vision, etc).

This module intentionally does nothing beyond validation. Background
removal and enhancement are separate gates (3 and 4) and must not be
implemented here.
"""

from io import BytesIO

from PIL import Image, UnidentifiedImageError

# Formats accepted for the hackathon MVP, per the Gate 2 spec.
ALLOWED_TYPES = {"JPEG", "PNG", "WEBP"}

# 10 MB, per the Gate 2 spec.
MAX_SIZE = 10 * 1024 * 1024

# Minimum practical resolution, per the master context doc (Section 8).
MIN_WIDTH = 300
MIN_HEIGHT = 300


def validate_image(data: bytes) -> Image.Image:
    """
    Validate raw image bytes.

    Checks (in order):
    1. File is not empty.
    2. File size does not exceed MAX_SIZE.
    3. File is a decodable, non-corrupted image.
    4. File format is one of ALLOWED_TYPES.
    5. Image resolution meets the minimum practical size.

    Returns the opened PIL Image on success.
    Raises ValueError with a human-readable message on any failure.
    """
    if not data:
        raise ValueError("Empty file")

    if len(data) > MAX_SIZE:
        raise ValueError("Image exceeds 10 MB")

    try:
        image = Image.open(BytesIO(data))
        image.verify()
        # Image.verify() leaves the file object unusable for further
        # operations, so it must be re-opened to actually read attributes
        # like width/height/format.
        image = Image.open(BytesIO(data))
        # Force a full decode (not just header parsing) to catch
        # truncated/corrupted image data that verify() can miss.
        image.load()
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError):
        raise ValueError("Invalid image")

    if image.format not in ALLOWED_TYPES:
        raise ValueError("Unsupported image format")

    if image.width < MIN_WIDTH or image.height < MIN_HEIGHT:
        raise ValueError("Image resolution too low")

    return image
