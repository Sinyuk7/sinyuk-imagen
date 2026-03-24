"""Image materialization helpers shared by provider implementations."""

from __future__ import annotations

import hashlib
import io
from pathlib import Path
import re
import shutil
import tempfile
from urllib.parse import urlsplit, urlunsplit

from PIL import Image

from core.generation._internal._provider_diagnostics import append_fact
from core.generation._internal._provider_resolution import (
    append_generated_image_resolution_fact,
)
from core.schemas import (
    DiagnosticCode,
    GeneratedImageArtifact,
    ProviderDiagnosticFact,
)


def detect_generated_image_extension(
    image_bytes: bytes,
    mime_type: str | None,
) -> str:
    """Infer the file extension for a generated image."""
    normalized_mime = (mime_type or "").split(";", 1)[0].strip().lower()
    mime_to_extension = {
        "image/gif": "gif",
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
    }
    if normalized_mime in mime_to_extension:
        return mime_to_extension[normalized_mime]

    try:
        with Image.open(io.BytesIO(image_bytes)) as parsed_image:
            image_format = (parsed_image.format or "").lower()
    except Exception:
        image_format = ""

    if image_format == "jpeg":
        return "jpg"
    if image_format:
        return image_format
    return "png"


def detect_generated_image_mime_type(
    image_bytes: bytes,
    mime_type: str | None,
) -> str:
    """Infer the mime type for a generated image."""
    normalized_mime = (mime_type or "").split(";", 1)[0].strip().lower()
    if normalized_mime:
        return normalized_mime

    extension_to_mime = {
        "gif": "image/gif",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
    }
    extension = detect_generated_image_extension(image_bytes, mime_type)
    return extension_to_mime.get(extension, "image/png")


def persist_generated_image_bytes(
    image_bytes: bytes,
    mime_type: str | None,
) -> tuple[str, str]:
    """Persist generated image bytes into the shared temp image cache."""
    extension = detect_generated_image_extension(image_bytes, mime_type)
    digest = hashlib.sha256(image_bytes).hexdigest()
    temp_dir = Path(tempfile.gettempdir()) / "sinyuk-imagen" / "generated-images"
    temp_dir.mkdir(parents=True, exist_ok=True)
    image_path = temp_dir / f"{digest}.{extension}"
    if not image_path.exists():
        image_path.write_bytes(image_bytes)
    return str(image_path), digest


def materialize_generated_image(
    *,
    image_bytes: bytes,
    mime_type: str | None,
    provider_name: str,
    model_name: str,
    requested_resolution: str | None,
    facts: list[ProviderDiagnosticFact],
    source_uri: str | None = None,
    source_kind: str = "inline_data",
) -> GeneratedImageArtifact:
    """Persist a generated image and return its richer artifact view."""
    canonical_path, content_hash = persist_generated_image_bytes(
        image_bytes=image_bytes,
        mime_type=mime_type,
    )
    resolved_mime_type = detect_generated_image_mime_type(image_bytes, mime_type)
    width, height = extract_image_dimensions(image_bytes)
    extension = detect_generated_image_extension(image_bytes, mime_type)
    download_name = build_download_name(
        provider_name=provider_name,
        model_name=model_name,
        content_hash=content_hash,
        extension=extension,
    )
    presentation_path = build_presentation_image_path(
        canonical_path=canonical_path,
        download_name=download_name,
        content_hash=content_hash,
    )
    artifact = GeneratedImageArtifact(
        canonical_path=canonical_path,
        presentation_path=presentation_path,
        download_name=download_name,
        mime_type=resolved_mime_type,
        width=width,
        height=height,
        content_hash=content_hash,
        source_uri=source_uri,
        source_kind=source_kind,
    )
    append_fact(
        facts,
        DiagnosticCode.GENERATED_IMAGE_MATERIALIZED,
        {
            "download_name": artifact.download_name,
            "mime_type": artifact.mime_type,
            "width": artifact.width,
            "height": artifact.height,
            "source_kind": artifact.source_kind,
        },
    )
    if source_uri:
        append_fact(
            facts,
            DiagnosticCode.GENERATED_IMAGE_SOURCE_RECORDED,
            {
                "source_kind": source_kind,
                "source_uri": sanitize_source_uri(source_uri),
            },
        )
    append_generated_image_resolution_fact(
        facts=facts,
        artifact=artifact,
        requested_resolution=requested_resolution,
        append_fact=append_fact,
    )
    return artifact


def extract_image_dimensions(image_bytes: bytes) -> tuple[int, int]:
    """Read width and height from raw image bytes."""
    with Image.open(io.BytesIO(image_bytes)) as parsed_image:
        return parsed_image.size


def slugify_filename_segment(value: str) -> str:
    """Build a filesystem-safe file-name segment."""
    slug = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-").lower()
    return slug or "image"


def build_download_name(
    *,
    provider_name: str,
    model_name: str,
    content_hash: str,
    extension: str,
) -> str:
    """Build a friendly download file name."""
    provider_slug = slugify_filename_segment(provider_name)
    model_slug = slugify_filename_segment(model_name)
    short_hash = content_hash[:12]
    return f"{provider_slug}-{model_slug}-{short_hash}.{extension}"


def build_presentation_image_path(
    *,
    canonical_path: str,
    download_name: str,
    content_hash: str,
) -> str:
    """Create a user-friendly copy used by Gradio downloads."""
    temp_dir = (
        Path(tempfile.gettempdir())
        / "sinyuk-imagen"
        / "generated-images-presentation"
        / content_hash
    )
    temp_dir.mkdir(parents=True, exist_ok=True)
    presentation_path = temp_dir / download_name
    if not presentation_path.exists():
        shutil.copy2(canonical_path, presentation_path)
    return str(presentation_path)


def sanitize_source_uri(value: str) -> str:
    """Remove query and fragment data from a source URI."""
    parts = urlsplit(value)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
