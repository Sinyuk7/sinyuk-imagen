"""
core/generation/_internal/reference_images - 参考图像预处理

INTENT: 提供参考图像的预处理和缓存功能
SIDE EFFECT: FILE_SYSTEM (创建缓存文件)
"""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

from core.schemas import PreparedReferenceImage
from core.utils import ImageUtils


class ReferenceImagePreparer:
    """
    参考图像预处理器

    INTENT: 将原始参考图像处理为适合 Provider 使用的格式
    SIDE EFFECT: FILE_SYSTEM (创建缓存文件)
    """

    def prepare(
        self,
        raw_reference_image_path: str | None,
        divisible_by: int,
        aspect_ratio: str | None,
    ) -> PreparedReferenceImage | None:
        """
        准备参考图像

        INTENT: 返回稳定的 prepared-reference 记录或 None
        INPUT:
            - raw_reference_image_path: 原始图像路径
            - divisible_by: 尺寸需要整除的值
            - aspect_ratio: 目标宽高比
        OUTPUT: PreparedReferenceImage 或 None
        SIDE EFFECT: FILE_SYSTEM (创建缓存文件)
        FAILURE: 抛出 FileNotFoundError (图像文件不存在)
        """
        if raw_reference_image_path is None:
            return None

        raw_path = Path(raw_reference_image_path)
        if not raw_path.exists():
            raise FileNotFoundError(f"Reference image not found at: {raw_reference_image_path}")

        cache_path = self._build_prepared_reference_path(raw_path, divisible_by, aspect_ratio)
        if cache_path.exists():
            from PIL import Image

            with Image.open(cache_path) as cached_img:
                width, height = cached_img.size
            return PreparedReferenceImage(
                raw_path=str(raw_path),
                prepared_path=str(cache_path),
                width=width,
                height=height,
                divisible_by=divisible_by,
                aspect_ratio=aspect_ratio,
            )

        processed_image = ImageUtils.preprocess(
            image_path=str(raw_path),
            divisible_by=divisible_by,
            aspect_ratio=aspect_ratio,
        )
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        processed_image.save(cache_path, format="PNG")
        width, height = processed_image.size
        processed_image.close()

        return PreparedReferenceImage(
            raw_path=str(raw_path),
            prepared_path=str(cache_path),
            width=width,
            height=height,
            divisible_by=divisible_by,
            aspect_ratio=aspect_ratio,
        )

    def _build_prepared_reference_path(
        self,
        raw_path: Path,
        divisible_by: int,
        aspect_ratio: str | None,
    ) -> Path:
        """
        构建缓存路径

        INTENT: 基于输入参数生成稳定的缓存文件路径
        INPUT:
            - raw_path: 原始图像路径
            - divisible_by: 尺寸整除值
            - aspect_ratio: 宽高比
        OUTPUT: 缓存文件路径
        SIDE EFFECT: None
        FAILURE: 无
        """
        stat = raw_path.stat()
        cache_key = json.dumps(
            {
                "raw_path": str(raw_path.resolve()),
                "mtime_ns": stat.st_mtime_ns,
                "size": stat.st_size,
                "divisible_by": divisible_by,
                "aspect_ratio": aspect_ratio,
                "mode": "crop",
                "max_dimension": 2048,
            },
            ensure_ascii=True,
            sort_keys=True,
        )
        digest = hashlib.sha256(cache_key.encode("utf-8")).hexdigest()
        temp_root = Path(tempfile.gettempdir()) / "sinyuk-imagen" / "prepared-reference-images"
        return temp_root / f"{digest}.png"
