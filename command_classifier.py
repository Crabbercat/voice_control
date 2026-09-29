from __future__ import annotations

import re
import unicodedata


# ============================================================
# COMMAND PHRASES
# ============================================================

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


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_text(text: str) -> str:
    """
    Normalize Vietnamese ASR text.

    - lowercase
    - remove Vietnamese diacritics
    - normalize đ -> d
    - normalize whitespace
    - remove punctuation
    """

    text = text.lower().strip()

    # Một số ASR có thể trả về dấu câu
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)

    # đ -> d
    text = text.replace("đ", "d")

    # Remove accents
    text = "".join(
        character
        for character in unicodedata.normalize("NFD", text)
        if unicodedata.category(character) != "Mn"
    )

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


# ============================================================
# ASR CORRECTION
# ============================================================

def correct_asr_text(text: str) -> str:
    """
    Correct only known ASR mistakes.

    IMPORTANT:
    Do not globally replace characters because that can
    completely change unrelated words.
    """

    replacements = {
        # cái -> cai
        "tái đèn": "cái đèn",
        "tái điện": "cái điện",
        "tái quạt": "cái quạt",

        # Một số trường hợp ASR có thể dính từ
        "batden": "bat den",
        "mo den": "mo den",
        "tat den": "tat den",
        "bat quat": "bat quat",
        "mo quat": "mo quat",
        "tat quat": "tat quat",
    }

    for wrong, correct in replacements.items():
        text = text.replace(wrong, correct)

    return text


# ============================================================
# COMMAND CLASSIFIER
# ============================================================

def classify_command(text: str) -> str:
    """
    Return:
        LIGHT_ON
        LIGHT_OFF
        FAN_ON
        FAN_OFF
        UNKNOWN
    """

    normalized_text = normalize_text(text)
    normalized_text = correct_asr_text(normalized_text)

    for command, phrases in COMMAND_PHRASES:
        for phrase in phrases:
            normalized_phrase = normalize_text(phrase)

            if normalized_phrase in normalized_text:
                return command

    return "UNKNOWN"


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    examples = (
        "BẬT   ĐÈN",
        "mở cái quạt trong phòng",
        "cho đèn tắt",
        "dừng quạt",
        "chúc mừng sinh nhật",

        # ASR mistakes
        "bật tái đèn",
        "mở tái quạt",

        # punctuation
        "Bật đèn!",
        "Tắt quạt.",

        # unrelated
        "bật máy lạnh",
        "mở cửa",
    )

    for example in examples:
        print(
            f"{example!r:30} -> {classify_command(example)}"
        )