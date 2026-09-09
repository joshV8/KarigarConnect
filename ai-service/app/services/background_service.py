"""
Background removal service — Gate 3.

Removes the photograph background while preserving the product itself.
Uses rembg for the MVP (see 14_IMPLEMENTATION_STATUS.md, Section 10 —
"Background Removal: rembg for MVP"). Do not train or wire in a custom
segmentation model here; that is out of scope for this gate.

This module intentionally does nothing beyond background removal.
Enhancement (contrast/brightness/sharpness) is Gate 4 and must not be
implemented here.
"""

from io import BytesIO

from PIL import Image

try:
    from rembg import remove
except ImportError:  # pragma: no cover - exercised only when rembg is missing
    remove = None


def remove_background(data: bytes) -> bytes:
    """
    Remove the background from a product photo.

    Args:
        data: raw bytes of the source image (already validated by
            Gate 2's validate_image() before reaching this function).

    Returns:
        PNG-encoded bytes with a transparent background around the
        product. Product geometry is not altered by this step; rembg
        only masks/removes background pixels, it does not repaint or
        invent product parts.

    Raises:
        RuntimeError: if the rembg package is not installed in this
            environment.
        ValueError: if the input cannot be processed into an image
            (e.g. rembg's output is not decodable).
    """
    if remove is None:
        raise RuntimeError(
            "rembg is not installed. Run `pip install rembg pillow` "
            "(see requirements.txt) before calling remove_background()."
        )

    result = remove(data)

    try:
        image = Image.open(BytesIO(result)).convert("RGBA")
    except Exception as exc:  # Image.open can raise several PIL error types
        raise ValueError(f"rembg produced an undecodable result: {exc}") from exc

    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()
