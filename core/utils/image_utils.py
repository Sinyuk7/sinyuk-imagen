import base64
import io
import logging
from typing import Optional, Tuple

from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

class ImageUtils:
    """图片预处理工具类 (极致优化版)"""

    @staticmethod
    def preprocess(
        image_path: str,
        divisible_by: int = 1,
        aspect_ratio: Optional[str] = None,
        max_dimension: int = 2048,
        mode: str = "crop"  # 新增：允许用户选择 crop 还是 pad
    ) -> Image.Image:
        
        img = Image.open(image_path)
        orig_w, orig_h = img.size
        
        # 1. 纯数学推导出最完美的“目标画框”尺寸
        target_w, target_h = ImageUtils._calculate_target_size(
            orig_w, orig_h, divisible_by, aspect_ratio, max_dimension
        )

        if (target_w, target_h) == (orig_w, orig_h):
            return img

        # 2. 调用 PIL.ImageOps 完美解决拉伸问题，且只处理一次！
        if mode == "crop":
            # 等比缩放，填满画框，多余裁掉 (ComfyUI / Midjourney 默认逻辑)
            return ImageOps.fit(img, (target_w, target_h), method=Image.Resampling.LANCZOS)
        
        elif mode == "pad":
            # 等比缩放，装进画框，不足的用黑边填补 (ControlNet 严格不丢像素逻辑)
            return ImageOps.pad(img, (target_w, target_h), method=Image.Resampling.LANCZOS, color=(0, 0, 0))
            
        else:
            raise ValueError("mode 必须是 'crop' 或 'pad'")
        

    @staticmethod
    def _calculate_target_size(
        w: int, 
        h: int, 
        divisible_by: int, 
        aspect_ratio: Optional[str], 
        max_dim: int
    ) -> Tuple[int, int]:
        """纯数学逻辑：计算最终的合法尺寸 (不操作图片本身)"""
        
        # 步骤 A: 计算比例目标
        if aspect_ratio and aspect_ratio != "original":
            try:
                rw, rh = map(float, aspect_ratio.split(":"))
                target_ratio = rw / rh
                current_ratio = w / h
                
                # 基于面积或短边基准，算出裁剪后的纯净宽高
                if current_ratio > target_ratio:
                    w = int(h * target_ratio)  # 切宽度
                else:
                    h = int(w / target_ratio)  # 切高度
            except (ValueError, ZeroDivisionError):
                logger.warning("Invalid aspect ratio '%s', ignored.", aspect_ratio)

        # 步骤 B: 约束最大尺寸 (保持前面的比例)
        if max_dim and (w > max_dim or h > max_dim):
            scale = min(max_dim / w, max_dim / h)
            w = int(w * scale)
            h = int(h * scale)

        # 步骤 C: 对齐 N 的倍数 (使用四舍五入，并确保不会超过 max_dim)
        if divisible_by > 1:
            w = max(divisible_by, round(w / divisible_by) * divisible_by)
            h = max(divisible_by, round(h / divisible_by) * divisible_by)
            
            # 对齐后如果超标了，强制降一档 (减去一个 N)
            if w > max_dim: w -= divisible_by
            if h > max_dim: h -= divisible_by

        return w, h

    @staticmethod
    def to_bytes(img: Image.Image, format: str = "PNG") -> bytes:
        """统一底层：转换为字节数据"""
        buffer = io.BytesIO()
        img.save(buffer, format=format)
        return buffer.getvalue()

    @staticmethod
    def to_base64(img: Image.Image, format: str = "PNG") -> str:
        """复用底层：转换为 Base64 字符串"""
        # 直接复用 to_bytes，消灭重复的 buffer 逻辑
        img_bytes = ImageUtils.to_bytes(img, format)
        return base64.b64encode(img_bytes).decode("utf-8")