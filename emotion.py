"""Emotion analysis and persona keyword extraction."""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

EMOTION_KEYWORDS: Dict[str, List[str]] = {
    "tsundere": ["哼", "才不是", "才没有", "谁管你", "别搞错", "才不", "谁要", "谁稀罕", "笨蛋", "变态"],
    "smug": ["哼哼", "本小姐", "轻轻松松", "这不就", "毫无悬念", "小菜一碟", "厉害吧", "佩服吧"],
    "sigh": ["唉", "无语", "头疼", "真是的", "服了", "受不了", "累了", "没救了", "救命"],
    "shock": ["哈？", "哈？！", "什么？！", "怎么可能", "真假", "假的吧", "纳尼", "卧槽"],
    "happy": ["哈哈", "嘿嘿", "太好了", "好耶", "开心", "有意思", "棒", "好玩"],
    "thinking": ["唔", "让我想想", "原来如此", "这样啊", "思考", "分析", "也就是说"],
}

DEFAULT_CAPTIONS: Dict[str, List[str]] = {
    "tsundere": ["哼！", "才不是呢！", "谁要管你啊！", "别自作多情！"],
    "smug": ["哼哼~", "小菜一碟！", "全看本小姐的！", "崇拜我吧！"],
    "sigh": ["唉...", "真是服了你...", "头疼喵...", "无语住了"],
    "shock": ["哈？！", "骗人的吧？！", "什么情况？！", "大受震撼！"],
    "happy": ["好耶！", "哈哈~", "超开心喵！", "太棒啦！"],
    "thinking": ["唔...", "思考中...", "让我想想喵", "真相是..."],
}

PROMPT_TAGS: Dict[str, str] = {
    "tsundere": "pout face, blush, crossed arms, angry cute expression, anime sticker",
    "smug": "smug smile, tilted head, confident grin, winking, anime sticker",
    "sigh": "sighing, facepalm, weary eyes, drooping cat ears, anime sticker",
    "shock": "shocked, wide eyes, open mouth, surprised, anime sticker",
    "happy": "happy smile, laughing, closed eyes joy, energetic, anime sticker",
    "thinking": "thinking, hand on chin, looking away, curious, anime sticker",
}


def detect_emotion(text: str) -> Tuple[str, str]:
    """Detect the most prominent emotion and select a caption from the text."""
    if not text:
        return "smug", "哼哼~"

    # Search for keywords
    scores: Dict[str, int] = {e: 0 for e in EMOTION_KEYWORDS}
    for emotion, kws in EMOTION_KEYWORDS.items():
        for kw in kws:
            if kw in text:
                scores[emotion] += text.count(kw)

    best_emotion = max(scores, key=lambda k: scores[k])
    if scores[best_emotion] == 0:
        # Fallback to question or exclamation based
        if "？" in text or "?" in text:
            best_emotion = "shock"
        elif "！" in text or "!" in text:
            best_emotion = "smug"
        else:
            best_emotion = "happy"

    # Try to extract short exclamation as caption from text
    # e.g., sentences with quotes or trailing !/?
    matches = re.findall(r"([「“][^」”]{1,8}[」”]|[\u4e00-\u9fa5]{1,6}[！!？?~]{1,2})", text)
    caption = matches[-1].strip("「」“”") if matches else DEFAULT_CAPTIONS[best_emotion][0]

    return best_emotion, caption
