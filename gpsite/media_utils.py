"""
Upload-time media processing -- the Python equivalent of the original app's
ImageProcessingService (SixLabors.ImageSharp) and VideoCompressionService
(Xabe.FFmpeg). Files are compressed before being handed to Django's storage
layer, so they work the same way whether MEDIA is on local disk or (later)
Azure Blob -- see MEDIA_ROOT/DEFAULT_FILE_STORAGE in settings.py.
"""

import subprocess
import tempfile
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image

MAX_WIDTH = 1280
MAX_HEIGHT = 720
JPEG_QUALITY = 75


def compress_image(uploaded_file, filename_hint="upload.jpg"):
    """
    Mirrors ImageProcessingService.CompressImageAsync: downscale to fit within
    1280x720 (preserving aspect ratio, never upscaling), re-encode as JPEG at
    quality 75 -- but only use the compressed version if it actually came out
    smaller than the original (small/already-optimised images are left alone).
    Returns a Django ContentFile ready to assign to a FileField/ImageField.
    """
    original_bytes = uploaded_file.read()
    uploaded_file.seek(0)

    image = Image.open(BytesIO(original_bytes))
    image = image.convert("RGB") if image.mode in ("RGBA", "P") else image
    image.thumbnail((MAX_WIDTH, MAX_HEIGHT), Image.LANCZOS)

    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    compressed_bytes = buffer.getvalue()

    stem = Path(filename_hint).stem or "upload"
    if len(compressed_bytes) < len(original_bytes):
        return ContentFile(compressed_bytes, name=f"{stem}.jpg")
    return ContentFile(original_bytes, name=filename_hint)


def compress_video(uploaded_file, filename_hint="upload.mp4", max_height=720):
    """
    Mirrors VideoCompressionService: re-encode to a max height of 720p via
    ffmpeg (`-vf scale=-2:720`), keeping aspect ratio. Runs synchronously --
    fine for a handful of short demo clips; a production version would push
    this to a background task queue instead of blocking the request.
    Returns a Django ContentFile of the compressed .mp4, or None if ffmpeg
    isn't available (caller should fall back to storing the raw upload).
    """
    ffmpeg_path = Path(settings.FFMPEG_PATH)
    if not ffmpeg_path.exists():
        return None

    with tempfile.TemporaryDirectory() as tmp_dir:
        input_path = Path(tmp_dir) / "input"
        output_path = Path(tmp_dir) / "output.mp4"

        with open(input_path, "wb") as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)

        result = subprocess.run(
            [
                str(ffmpeg_path), "-y", "-i", str(input_path),
                "-vf", f"scale=-2:{max_height}",
                "-c:v", "libx264", "-preset", "fast", "-crf", "28",
                "-c:a", "aac", "-b:a", "128k",
                str(output_path),
            ],
            capture_output=True,
            timeout=300,
        )
        if result.returncode != 0 or not output_path.exists():
            return None

        stem = Path(filename_hint).stem or "video"
        return ContentFile(output_path.read_bytes(), name=f"{stem}.mp4")
