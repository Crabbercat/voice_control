from __future__ import annotations

import re
import unicodedata


LIGHT_ON_PHRASES = (
    "bật cái đèn",
    "mở cái đèn",
    "bật điện",
    "mở điện",
    "cho đèn sáng",
    "bật đèn",
    "mở đèn",
)
LIGHT_OFF_PHRASES = (
    "tắt cái đèn",
    "tắt điện",
    "tắt cái điện",
    "đóng cái đèn",
    "cho đèn tắt",
    "tắt đèn",
    "đóng đèn",
)
FAN_ON_PHRASES = (
    "bật cái quạt",
    "mở cái quạt",
    "cho quạt chạy",
    "bật quạt",
    "mở quạt",
)
FAN_OFF_PHRASES = (
    "tắt cái quạt",
    "đóng cái quạt",
    "dừng quạt",
    "tắt quạt",
    "đóng quạt",
)

COMMAND_PHRASES = (
    ("LIGHT_ON", LIGHT_ON_PHRASES),
    ("LIGHT_OFF", LIGHT_OFF_PHRASES),
    ("FAN_ON", FAN_ON_PHRASES),
    ("FAN_OFF", FAN_OFF_PHRASES),
)


def normalize_text(text: str) -> str:
    """Normalize Vietnamese text and common ASR character confusions."""
    text = text.lower().replace("đ", "d")
    text = "".join(
        character
        for character in unicodedata.normalize("NFD", text)
        if unicodedata.category(character) != "Mn"
    )
    text = re.sub(r"\s+", " ", text).strip()
    return text.replace("c", "t")


def classify_command(text: str) -> str:
    """Return the matching IoT command, or UNKNOWN when no phrase matches."""
    normalized_text = normalize_text(text)
    for command, phrases in COMMAND_PHRASES:
        if any(normalize_text(phrase) in normalized_text for phrase in phrases):
            return command
    return "UNKNOWN"


if __name__ == "__main__":
    examples = (
        "BẬT   ĐÈN",
        "mở cái quạt trong phòng",
        "cho đèn tắt",
        "dừng quạt",
        "chúc mừng sinh nhật",
    )
    for example in examples:
        print(f"{example!r} -> {classify_command(example)}")
