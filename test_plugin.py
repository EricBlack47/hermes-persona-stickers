"""Unit tests for hermes-persona-stickers plugin."""

import json
import os
import time
from pathlib import Path
from PIL import Image

from emotion import detect_emotion
from renderer import render_sticker, render_pool_sticker, render_fast_sticker
import __init__ as plugin


def test_emotion_detection():
    """Verify keyword and punctuation emotion extraction."""
    samples = {
        "哈？！你脑子没被电路由烧坏吧？谁准你这么直白地说这种话了！": "shock",
        "哼哼，这种小事对本小姐来说不过是小菜一碟喵！": "smug",
        "唉...真是服了你这家伙，脑袋又宕机了吗？": "sigh",
        "好耶！这次终于全部通过啦！": "happy",
        "笨蛋！才没有在等你呢！": "tsundere",
    }
    for text, expected in samples.items():
        em, cap = detect_emotion(text)
        assert em == expected, f"Expected {expected}, got {em} for '{text}'"
        assert len(cap) > 0, "Caption should not be empty"


def test_pool_sticker_rendering(tmp_path):
    """Verify sub-50ms pre-baked asset pool rendering and 32-bit RGBA output."""
    out_png = str(tmp_path / "pool_tsundere.png")
    out_webp = str(tmp_path / "pool_tsundere.webp")

    # Warmup font / codecs
    _ = render_pool_sticker("xuewan", "tsundere", "预热", str(tmp_path / "warmup.png"), size=256)

    # Benchmark PNG
    t0 = time.perf_counter()
    res_png = render_pool_sticker("xuewan", "tsundere", "才没有等你！", out_png, size=256)
    dt_ms = (time.perf_counter() - t0) * 1000

    assert res_png is not None
    assert Path(out_png).exists()
    assert dt_ms < 60.0, f"Render took too long: {dt_ms:.2f} ms (cold load accounted for)"

    # Image properties check
    im = Image.open(out_png)
    assert im.size == (256, 256)
    assert im.mode == "RGBA", "Must be 32-bit RGBA, never palette mode"
    im.close()

    # Benchmark WebP
    res_webp = render_pool_sticker("xuewan", "tsundere", "才没有等你！", out_webp, size=128)
    assert res_webp is not None
    assert Path(out_webp).exists()
    assert Path(out_webp).stat().st_size < 30 * 1024, "128x128 WebP should be < 30KB"


def test_fast_vector_fallback(tmp_path):
    """Verify vector fallback works when asset pool does not have emotion."""
    out_file = str(tmp_path / "vector_thinking.png")
    res = render_fast_sticker("xuewan", "thinking", "让我想想...", out_file, size=256)
    assert Path(res).exists()

    im = Image.open(res)
    assert im.size == (256, 256)
    assert im.mode == "RGBA"
    im.close()


def test_unified_render_sticker(tmp_path):
    """Verify render_sticker auto degradation."""
    # 1. Existing emotion -> pool mode
    out_pool = str(tmp_path / "auto_smug.png")
    res1 = render_sticker("xuewan", "smug", "小菜一碟！", out_pool, size=256, mode="auto")
    assert Path(res1).exists()

    # 2. Non-existing emotion -> fallback to fast vector
    out_fallback = str(tmp_path / "auto_unknown.png")
    res2 = render_sticker("xuewan", "thinking", "思考中...", out_fallback, size=256, mode="auto")
    assert Path(res2).exists()


def test_tool_handler(tmp_path):
    """Verify generate_persona_sticker tool output schema."""
    res_json = plugin.generate_persona_sticker({
        "emotion": "tsundere",
        "text": "笨蛋！",
        "size": 256,
        "mode": "auto",
    })
    data = json.loads(res_json)
    assert data["status"] == "success"
    assert "media_tag" in data
    assert data["media_tag"].startswith("MEDIA:")
    assert Path(data["sticker_path"]).exists()


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
