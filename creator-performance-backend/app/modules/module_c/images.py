"""Shared, full-frame image handling. No upload is written to disk."""

import base64
import hashlib
import io
import warnings

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

PREPROCESSING_VERSION = "rgb-exif-fullframe-graypad-v1"
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}


def load_image(data: bytes, max_pixels: int = 25_000_000) -> Image.Image:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as source:
                if source.format not in ALLOWED_FORMATS:
                    raise ValueError("Use a JPEG, PNG, or WebP image.")
                if source.width * source.height > max_pixels or min(source.size) < 16:
                    raise ValueError(
                        "Image dimensions must be at least 16 pixels and within the pixel limit."
                    )
                if getattr(source, "n_frames", 1) != 1:
                    raise ValueError("Animated images are unsupported.")
                source.load()
                oriented = ImageOps.exif_transpose(source)
                if oriented.mode in ("RGBA", "LA") or "transparency" in oriented.info:
                    rgba = oriented.convert("RGBA")
                    background = Image.new("RGBA", rgba.size, (127, 127, 127, 255))
                    return Image.alpha_composite(background, rgba).convert("RGB")
                return oriented.convert("RGB")
    except (
        UnidentifiedImageError,
        OSError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ) as exc:
        raise ValueError("The image could not be safely decoded.") from exc


def image_hash(image: Image.Image) -> str:
    # Decoded-pixel identity also catches copies with different metadata/file names.
    digest = hashlib.sha256(str(image.size).encode())
    digest.update(image.tobytes())
    return digest.hexdigest()


def difference_hash(image: Image.Image) -> int:
    gray = np.asarray(image.convert("L").resize((9, 8), Image.Resampling.LANCZOS))
    result = 0
    for bit in (gray[:, 1:] > gray[:, :-1]).ravel():
        result = (result << 1) | int(bit)
    return result


def square_image(image: Image.Image) -> Image.Image:
    # The CLIP processor subsequently applies its own resize/normalization.
    # Padding prevents its square center crop from discarding side text/subjects.
    size = max(image.size)
    canvas = Image.new("RGB", (size, size), (127, 127, 127))
    canvas.paste(image, ((size - image.width) // 2, (size - image.height) // 2))
    return canvas


def mobile_preview(image: Image.Image) -> str:
    preview = ImageOps.pad(image, (320, 180), color=(127, 127, 127), method=Image.Resampling.LANCZOS)
    output = io.BytesIO()
    preview.save(output, format="JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(output.getvalue()).decode("ascii")
