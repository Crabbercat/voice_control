from __future__ import annotations

import re


LIGHT_ON_PHRASES = (
    "bật cái đèn",
    "mở cái đèn",
    "cho đèn sáng",
    "bật đèn",
    "mở đèn",
)
LIGHT_OFF_PHRASES = (
    "tắt cái đèn",
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
    """Lowercase text and collapse repeated whitespace."""
    return re.sub(r"\s+", " ", text.lower()).strip()


def classify_command(text: str) -> str:
    """Return the matching IoT command, or UNKNOWN when no phrase matches."""
    normalized_text = normalize_text(text)
    for command, phrases in COMMAND_PHRASES:
        if any(phrase in normalized_text for phrase in phrases):
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
