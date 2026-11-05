"""Dual-engine sticker renderer: Pre-baked Asset Pool + Fast Pillow Vector Templating."""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

# Base assets directory within plugin
_ASSETS_DIR = Path(__file__).parent / "assets" / "personas"


def _find_system_font(size: int) -> ImageFont.ImageFont:
    """Find a readable bold font for comic captions across Linux and Windows."""
    candidates = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "C:\\Windows\\Fonts\\msyhbd.ttc",
        "C:\\Windows\\Fonts\\msyh.ttc",
        "C:\\Windows\\Fonts\\simhei.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _draw_text_with_outline(
    draw: ImageDraw.ImageDraw,
    xy: Tuple[int, int],
    text: str,
    font: ImageFont.ImageFont,
    fill_color: str | Tuple[int, int, int, int] = "#FFFFFF",
    outline_color: str | Tuple[int, int, int, int] = "#1A1A1A",
    outline_width: int = 4,
) -> None:
    x, y = xy
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx * dx + dy * dy <= outline_width * outline_width:
                draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
    draw.text((x, y), text, font=font, fill=fill_color)


def render_pool_sticker(
    persona_name: str,
    emotion: str,
    caption: str,
    output_path: str,
    size: int = 256,
) -> Optional[str]:
    """Render a reaction sticker in <30ms using pre-baked character asset pool.

    Guarantees standard 32-bit RGBA PNG or RGBA WebP output (never 8-bit palette),
    preventing Telegram Bot API from downgrading image to document attachment.
    """
    t0 = time.perf_counter()
    pool_dir = _ASSETS_DIR / persona_name
    if not pool_dir.exists():
        logger.debug("Persona pool directory does not exist: %s", pool_dir)
        return None

    # Try resolution-matched base first for zero resampling overhead
    target_base = pool_dir / f"{emotion}_{size}.png"
    if not target_base.exists():
        target_base = pool_dir / f"{emotion}.png"
    if not target_base.exists():
        target_base = pool_dir / f"{emotion}_{size}.webp"
    if not target_base.exists():
        target_base = pool_dir / f"{emotion}.webp"

    if not target_base.exists():
        logger.debug("No base asset found for emotion %s in %s", emotion, pool_dir)
        return None

    try:
        im = Image.open(target_base).convert("RGBA")
    except Exception as e:
        logger.warning("Failed to open base asset %s: %s", target_base, e)
        return None

    if im.size != (size, size):
        im = im.resize((size, size), Image.Resampling.BILINEAR)

    # Adaptive font sizing and strokes
    if size == 256:
        font_size = 19
        stroke_w = 4
        shadow_w = 2
        bottom_offset = 12
    elif size == 128:
        font_size = 11
        stroke_w = 2
        shadow_w = 1
        bottom_offset = 6
    else:  # 512
        font_size = 38
        stroke_w = 7
        shadow_w = 4
        bottom_offset = 24

    font = _find_system_font(font_size)
    draw = ImageDraw.Draw(im)
    bbox = draw.textbbox((0, 0), caption, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = max(2, (size - tw) // 2)
    y = size - th - bottom_offset

    # Dynamic 3-layer comic caption
    # Layer 1: Dark plum shadow
    draw.text(
        (x + 1, y + 1),
        caption,
        font=font,
        fill=(35, 15, 25, 220),
        stroke_width=shadow_w,
        stroke_fill=(35, 15, 25, 220),
    )
    # Layer 2: Clean white outer stroke
    draw.text(
        (x, y),
        caption,
        font=font,
        fill=(255, 255, 255, 255),
        stroke_width=stroke_w,
        stroke_fill=(255, 255, 255, 255),
    )
    # Layer 3: Vibrant Hot Pink inner text
    draw.text(
        (x, y),
        caption,
        font=font,
        fill=(255, 51, 102, 255),
        stroke_width=1,
        stroke_fill=(255, 255, 255, 255),
    )

    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    # Standard 32-bit RGBA export (strictly avoid palette mode for Telegram compatibility)
    ext = out_p.suffix.lower()
    if ext == ".webp":
        im.save(str(out_p), format="WEBP", quality=85, alpha_quality=85, method=2)
    else:
        im.save(str(out_p), format="PNG", compress_level=3)

    dt_ms = (time.perf_counter() - t0) * 1000
    logger.info("Pool sticker rendered in %.2f ms -> %s", dt_ms, output_path)
    return str(out_p)


def _draw_chibi_avatar(draw: ImageDraw.ImageDraw, emotion: str, center: Tuple[int, int], radius: int = 140) -> None:
    """Draw a vector chibi catgirl avatar based on emotion."""
    cx, cy = center
    face_color = "#FFF5EE"
    hair_color = "#E6E6FA"
    eye_color = "#00CED1"
    blush_color = "#FFB6C1"
    line_color = "#2F4F4F"

    # Cat Ears
    ear_left = [(cx - radius + 10, cy - radius // 2), (cx - radius - 20, cy - radius - 40), (cx - 20, cy - radius)]
    ear_right = [(cx + radius - 10, cy - radius // 2), (cx + radius + 20, cy - radius - 40), (cx + 20, cy - radius)]
    draw.polygon(ear_left, fill=hair_color, outline=line_color, width=4)
    draw.polygon(ear_right, fill=hair_color, outline=line_color, width=4)

    inner_left = [(cx - radius + 25, cy - radius // 2 + 5), (cx - radius - 8, cy - radius - 25), (cx - 30, cy - radius + 20)]
    inner_right = [(cx + radius - 25, cy - radius // 2 + 5), (cx + radius + 8, cy - radius - 25), (cx + 30, cy - radius + 20)]
    draw.polygon(inner_left, fill=blush_color)
    draw.polygon(inner_right, fill=blush_color)

    # Face
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=face_color, outline=line_color, width=4)

    # Twin Tails
    draw.ellipse([cx - radius - 50, cy - 30, cx - radius + 30, cy + 120], fill=hair_color, outline=line_color, width=3)
    draw.ellipse([cx + radius - 30, cy - 30, cx + radius + 50, cy + 120], fill=hair_color, outline=line_color, width=3)

    # Bangs
    bangs = [(cx - radius + 15, cy - radius + 40), (cx - radius // 2, cy - 10), (cx, cy - radius + 30),
             (cx + radius // 2, cy - 10), (cx + radius - 15, cy - radius + 40), (cx, cy - radius - 10)]
    draw.polygon(bangs, fill=hair_color, outline=line_color, width=3)

    # Eyes & Expression
    eye_y = cy + 10
    if emotion in ("tsundere", "angry"):
        draw.line([cx - 70, eye_y - 15, cx - 25, eye_y], fill=line_color, width=5)
        draw.line([cx + 25, eye_y, cx + 70, eye_y - 15], fill=line_color, width=5)
        draw.ellipse([cx - 60, eye_y, cx - 35, eye_y + 25], fill=eye_color)
        draw.ellipse([cx + 35, eye_y, cx + 60, eye_y + 25], fill=eye_color)
        draw.ellipse([cx - 85, eye_y + 25, cx - 45, eye_y + 45], fill=blush_color)
        draw.ellipse([cx + 45, eye_y + 25, cx + 85, eye_y + 45], fill=blush_color)
        draw.arc([cx - 20, eye_y + 35, cx, eye_y + 55], start=0, end=180, fill=line_color, width=4)
        draw.arc([cx, eye_y + 35, cx + 20, eye_y + 55], start=0, end=180, fill=line_color, width=4)
    elif emotion in ("smug", "happy"):
        draw.arc([cx - 70, eye_y - 10, cx - 20, eye_y + 20], start=180, end=360, fill=line_color, width=5)
        draw.arc([cx + 20, eye_y - 10, cx + 70, eye_y + 20], start=180, end=360, fill=line_color, width=5)
        draw.chord([cx - 25, eye_y + 35, cx + 25, eye_y + 65], start=0, end=180, fill="#FF6B81", outline=line_color, width=3)
        draw.ellipse([cx - 80, eye_y + 20, cx - 50, eye_y + 35], fill=blush_color)
        draw.ellipse([cx + 50, eye_y + 20, cx + 80, eye_y + 35], fill=blush_color)
    elif emotion == "sigh":
        draw.line([cx - 70, eye_y + 10, cx - 25, eye_y + 10], fill=line_color, width=4)
        draw.line([cx + 25, eye_y + 10, cx + 70, eye_y + 10], fill=line_color, width=4)
        draw.line([cx - 20, eye_y + 45, cx + 20, eye_y + 45], fill=line_color, width=4)
        draw.ellipse([cx + radius - 40, cy - 30, cx + radius - 15, cy - 5], fill="#00BFFF")
    elif emotion == "shock":
        draw.ellipse([cx - 70, eye_y - 20, cx - 20, eye_y + 30], fill="#FFFFFF", outline=line_color, width=4)
        draw.ellipse([cx + 20, eye_y - 20, cx + 70, eye_y + 30], fill="#FFFFFF", outline=line_color, width=4)
        draw.ellipse([cx - 52, eye_y - 5, cx - 38, eye_y + 15], fill=eye_color)
        draw.ellipse([cx + 38, eye_y - 5, cx + 52, eye_y + 15], fill=eye_color)
        draw.ellipse([cx - 20, eye_y + 35, cx + 20, eye_y + 75], fill="#FF4500", outline=line_color, width=3)
    else:  # thinking / default
        draw.ellipse([cx - 65, eye_y - 10, cx - 25, eye_y + 25], fill=eye_color, outline=line_color, width=3)
        draw.ellipse([cx + 25, eye_y - 10, cx + 65, eye_y + 25], fill=eye_color, outline=line_color, width=3)
        draw.arc([cx - 20, eye_y + 40, cx + 20, eye_y + 60], start=0, end=180, fill=line_color, width=4)


def render_fast_sticker(
    persona_name: str,
    emotion: str,
    caption: str,
    output_path: str,
    size: int = 256,
) -> str:
    """Zero-dependency vector chibi catgirl fallback renderer (<50ms)."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    scale = size / 512.0
    radius = int(135 * scale)
    cx, cy = size // 2, int((size // 2 - 30) * scale + 15)

    glow_color = (255, 230, 240, 180) if emotion == "tsundere" else (230, 245, 255, 180)
    pad = int(15 * scale)
    draw.ellipse([pad, pad, size - pad, size - int(35 * scale)], fill=glow_color, outline="#FFFFFF", width=max(2, int(6 * scale)))

    _draw_chibi_avatar(draw, emotion, center=(cx, cy), radius=radius)

    font_size = max(10, int((42 if len(caption) <= 6 else 30) * scale))
    font = _find_system_font(font_size)
    bbox = draw.textbbox((0, 0), caption, font=font)
    text_w = bbox[2] - bbox[0]
    text_x = (size - text_w) // 2
    text_y = size - int(45 * scale)

    text_color = "#FF1493" if emotion == "tsundere" else ("#FF8C00" if emotion == "shock" else "#1E90FF")
    _draw_text_with_outline(
        draw,
        (text_x, text_y),
        caption,
        font=font,
        fill_color=text_color,
        outline_color="#FFFFFF",
        outline_width=max(2, int(4 * scale)),
    )

    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(out_p), "PNG")
    return str(out_p)


def render_sticker(
    persona_name: str,
    emotion: str,
    caption: str,
    output_path: str,
    size: int = 256,
    mode: str = "auto",
) -> str:
    """Unified entry point with automatic graceful degradation.

    mode:
      - 'auto': try pre-baked asset pool first, gracefully fallback to fast vector
      - 'pool': strictly use asset pool
      - 'fast': strictly use vector template
    """
    if mode in ("auto", "pool"):
        res = render_pool_sticker(persona_name, emotion, caption, output_path, size=size)
        if res:
            return res
        if mode == "pool":
            raise RuntimeError(f"Asset pool sticker missing for {persona_name}/{emotion}")

    return render_fast_sticker(persona_name, emotion, caption, output_path, size=size)
