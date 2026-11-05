"""Hermes Persona Stickers Plugin — Persona-aware real-time emotion reaction generator."""

from __future__ import annotations

import json
import logging
import os
import random
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from .emotion import detect_emotion, PROMPT_TAGS
    from .renderer import render_sticker, render_fast_sticker, render_pool_sticker
except ImportError:
    from emotion import detect_emotion, PROMPT_TAGS
    from renderer import render_sticker, render_fast_sticker, render_pool_sticker

logger = logging.getLogger(__name__)

_DEFAULT_OUTPUT_DIR = Path.home() / ".hermes" / "stickers"


def generate_persona_sticker(args: Dict[str, Any], **kwargs: Any) -> str:
    """Tool handler for generating a persona reaction sticker.

    Args:
        emotion: tsundere, smug, sigh, shock, happy, thinking
        text: short caption text to put on the sticker
        size: 128, 256, or 512 (default 256)
        mode: 'auto', 'pool', or 'fast'
    """
    emotion = str(args.get("emotion") or "smug").lower()
    caption = str(args.get("text") or args.get("caption") or "哼哼~")
    size = int(args.get("size") or 256)
    mode = str(args.get("mode") or "auto").lower()

    out_dir = _DEFAULT_OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"sticker_{emotion}_{random.randint(1000, 9999)}.png"

    path = render_sticker(
        persona_name="xuewan",
        emotion=emotion,
        caption=caption,
        output_path=str(out_file),
        size=size,
        mode=mode,
    )

    return json.dumps({
        "status": "success",
        "sticker_path": path,
        "emotion": emotion,
        "caption": caption,
        "size": f"{size}x{size}",
        "media_tag": f"MEDIA:{path}",
    })


def _on_post_llm_call(message: Any, **kwargs: Any) -> Optional[str]:
    """Hook called after an LLM turn to optionally attach an emotion sticker."""
    text = getattr(message, "content", None) or str(message)
    if not text or len(text) < 15:
        return None

    # Determine emotion
    emotion, caption = detect_emotion(text)
    logger.debug("Detected emotion %s with caption %s", emotion, caption)
    return None


def _handle_slash_sticker(raw_args: str) -> str:
    """Handle /sticker command: e.g. /sticker tsundere 哼！"""
    parts = raw_args.strip().split(maxsplit=1)
    emotion = parts[0] if parts else "smug"
    caption = parts[1] if len(parts) > 1 else "哼哼~"

    out_dir = _DEFAULT_OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"sticker_cmd_{random.randint(1000, 9999)}.png"

    path = render_sticker(
        persona_name="xuewan",
        emotion=emotion,
        caption=caption,
        output_path=str(out_file),
        size=256,
        mode="auto",
    )
    return f"Generated {emotion} sticker:\nMEDIA:{path}"


def register(ctx: Any) -> None:
    """Plugin entry point for Hermes Agent."""
    schema = {
        "name": "generate_persona_sticker",
        "description": "Generate a persona-aware reaction sticker (sub-30ms) with styled comic captions.",
        "parameters": {
            "type": "object",
            "properties": {
                "emotion": {
                    "type": "string",
                    "enum": ["tsundere", "smug", "sigh", "shock", "happy", "thinking"],
                    "description": "Core emotion expression.",
                },
                "text": {
                    "type": "string",
                    "description": "Short comic caption on the sticker (e.g., '哼！', '小菜一碟！').",
                },
                "size": {
                    "type": "integer",
                    "enum": [128, 256, 512],
                    "default": 256,
                    "description": "Output sticker square resolution.",
                },
                "mode": {
                    "type": "string",
                    "enum": ["auto", "pool", "fast"],
                    "default": "auto",
                    "description": "Rendering mode: 'auto' (pool with fast fallback), 'pool' (pre-baked pool), 'fast' (pure vector).",
                },
            },
            "required": ["emotion"],
        },
    }
    ctx.register_tool(
        name="generate_persona_sticker",
        toolset="stickers",
        schema=schema,
        handler=generate_persona_sticker,
        description="Generate a persona-aware reaction sticker with comic caption text.",
        emoji="🐱",
    )

    ctx.register_hook("post_llm_call", _on_post_llm_call)

    ctx.register_command(
        "sticker",
        handler=_handle_slash_sticker,
        description="Generate a persona sticker on demand: /sticker <emotion> [text]",
    )
