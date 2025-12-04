"""Image optimization tools for WordPress media."""

import io
import os
import requests
from pathlib import Path
from typing import Optional, Literal
from PIL import Image
from dataclasses import dataclass

from .config import WordPressConfig


@dataclass
class ImageInfo:
    """Image metadata and analysis."""
    url: str
    format: str
    width: int
    height: int
    file_size: int
    file_size_kb: float
    has_transparency: bool
    mode: str


@dataclass
class OptimizationResult:
    """Result of image optimization."""
    original_size: int
    optimized_size: int
    savings_bytes: int
    savings_percent: float
    format: str
    width: int
    height: int


class ImageOptimizer:
    """Optimize images for web performance and SEO."""

    def __init__(self, config: WordPressConfig):
        self.config = config
        self.session = requests.Session()
        self.session.auth = (config.api_user, config.api_password)

    def download_image(self, url: str) -> tuple[Image.Image, ImageInfo]:
        """
        Download image from URL and return PIL Image with metadata.

        Args:
            url: Image URL (can be WordPress media URL)

        Returns:
            Tuple of (PIL Image, ImageInfo)
        """
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        image_data = response.content
        img = Image.open(io.BytesIO(image_data))

        info = ImageInfo(
            url=url,
            format=img.format or "UNKNOWN",
            width=img.width,
            height=img.height,
            file_size=len(image_data),
            file_size_kb=len(image_data) / 1024,
            has_transparency=img.mode in ("RGBA", "LA") or (
                img.mode == "P" and "transparency" in img.info
            ),
            mode=img.mode,
        )

        return img, info

    def convert_to_webp(
        self,
        img: Image.Image,
        quality: int = 85,
        lossless: bool = False
    ) -> bytes:
        """
        Convert image to WebP format.

        Args:
            img: PIL Image to convert
            quality: Quality setting (1-100), higher is better
            lossless: Use lossless compression (larger files)

        Returns:
            WebP image as bytes
        """
        output = io.BytesIO()

        # Convert RGBA to RGB if no transparency needed
        if img.mode == "RGBA" and not self._has_alpha_channel(img):
            img = img.convert("RGB")

        save_kwargs = {
            "format": "WEBP",
            "quality": quality,
        }

        if lossless:
            save_kwargs["lossless"] = True
        else:
            save_kwargs["method"] = 6  # Slowest but best compression

        img.save(output, **save_kwargs)
        return output.getvalue()

    def compress_image(
        self,
        img: Image.Image,
        format: Optional[str] = None,
        quality: int = 85,
        max_width: Optional[int] = None,
        max_height: Optional[int] = None
    ) -> bytes:
        """
        Compress image while maintaining format.

        Args:
            img: PIL Image to compress
            format: Output format (JPEG, PNG, WebP) - uses original if None
            quality: Quality setting for lossy formats
            max_width: Resize if wider than this
            max_height: Resize if taller than this

        Returns:
            Compressed image as bytes
        """
        # Resize if needed
        if max_width or max_height:
            img = self._resize_image(img, max_width, max_height)

        # Determine output format
        output_format = format or img.format or "JPEG"

        # Convert mode if needed
        if output_format == "JPEG" and img.mode in ("RGBA", "LA", "P"):
            # JPEG doesn't support transparency
            rgb_img = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            rgb_img.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
            img = rgb_img

        output = io.BytesIO()

        save_kwargs = {"format": output_format}

        if output_format in ("JPEG", "WEBP"):
            save_kwargs["quality"] = quality
            save_kwargs["optimize"] = True

        if output_format == "PNG":
            save_kwargs["optimize"] = True

        img.save(output, **save_kwargs)
        return output.getvalue()

    def optimize_image(
        self,
        url: str,
        target_format: Literal["webp", "jpeg", "png", "auto"] = "auto",
        quality: int = 85,
        max_width: int = 2048,
        max_height: int = 2048
    ) -> tuple[bytes, OptimizationResult]:
        """
        Download and optimize an image.

        Args:
            url: Image URL to optimize
            target_format: Desired output format (auto = choose best)
            quality: Quality setting (1-100)
            max_width: Maximum width in pixels
            max_height: Maximum height in pixels

        Returns:
            Tuple of (optimized image bytes, optimization result)
        """
        img, info = self.download_image(url)

        # Auto-select format
        if target_format == "auto":
            # Use WebP for most cases, PNG only if transparency needed
            if info.has_transparency:
                target_format = "webp"  # WebP supports transparency
            else:
                target_format = "webp"  # WebP is generally better than JPEG

        # Optimize
        if target_format == "webp":
            optimized_data = self.convert_to_webp(img, quality=quality)
        else:
            optimized_data = self.compress_image(
                img,
                format=target_format.upper(),
                quality=quality,
                max_width=max_width,
                max_height=max_height
            )

        # Calculate savings
        result = OptimizationResult(
            original_size=info.file_size,
            optimized_size=len(optimized_data),
            savings_bytes=info.file_size - len(optimized_data),
            savings_percent=((info.file_size - len(optimized_data)) / info.file_size * 100)
            if info.file_size > 0 else 0,
            format=target_format,
            width=img.width,
            height=img.height,
        )

        return optimized_data, result

    def analyze_wordpress_image(self, media_id: int) -> dict:
        """
        Analyze a WordPress media library image.

        Args:
            media_id: WordPress media attachment ID

        Returns:
            Analysis including size, format, alt text, optimization potential
        """
        # Get media details from WordPress API
        url = f"{self.config.site_url.rstrip('/')}/wp-json/wp/v2/media/{media_id}"
        response = self.session.get(url, timeout=30)
        response.raise_for_status()

        media_data = response.json()

        # Get image URL
        image_url = media_data.get("source_url", "")
        alt_text = media_data.get("alt_text", "")
        title = media_data.get("title", {}).get("rendered", "")

        # Download and analyze
        img, info = self.download_image(image_url)

        # Estimate WebP savings (rough estimate: 25-35% smaller)
        estimated_webp_size = info.file_size * 0.70
        estimated_savings = info.file_size - estimated_webp_size

        return {
            "media_id": media_id,
            "url": image_url,
            "title": title,
            "alt_text": alt_text,
            "has_alt_text": bool(alt_text),
            "current_format": info.format,
            "dimensions": f"{info.width}x{info.height}",
            "file_size_kb": round(info.file_size_kb, 2),
            "has_transparency": info.has_transparency,
            "recommendations": self._get_image_recommendations(info, alt_text),
            "estimated_webp_savings_kb": round(estimated_savings / 1024, 2),
            "estimated_webp_savings_percent": 30,
        }

    def _resize_image(
        self,
        img: Image.Image,
        max_width: Optional[int],
        max_height: Optional[int]
    ) -> Image.Image:
        """Resize image maintaining aspect ratio."""
        if not max_width and not max_height:
            return img

        width, height = img.size

        # Calculate new dimensions
        if max_width and width > max_width:
            ratio = max_width / width
            width = max_width
            height = int(height * ratio)

        if max_height and height > max_height:
            ratio = max_height / height
            height = max_height
            width = int(width * ratio)

        if (width, height) != img.size:
            img = img.resize((width, height), Image.Resampling.LANCZOS)

        return img

    def _has_alpha_channel(self, img: Image.Image) -> bool:
        """Check if image actually uses transparency."""
        if img.mode != "RGBA":
            return False

        # Check if alpha channel has any non-255 values
        alpha = img.split()[-1]
        return alpha.getextrema()[0] < 255

    def _get_image_recommendations(self, info: ImageInfo, alt_text: str) -> list[str]:
        """Generate optimization recommendations."""
        recommendations = []

        # Format recommendations
        if info.format in ("PNG", "JPEG") and not info.has_transparency:
            recommendations.append(
                f"Convert from {info.format} to WebP for ~30% file size reduction"
            )

        # Size recommendations
        if info.file_size_kb > 500:
            recommendations.append(
                f"Large file size ({info.file_size_kb:.1f}KB) - consider compression"
            )

        if info.width > 2048 or info.height > 2048:
            recommendations.append(
                f"Large dimensions ({info.width}x{info.height}) - resize for web"
            )

        # Alt text
        if not alt_text:
            recommendations.append("Missing alt text - important for SEO and accessibility")
        elif len(alt_text) < 10:
            recommendations.append("Alt text is very short - add more description")

        return recommendations
