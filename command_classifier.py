from __future__ import annotations

import re
import unicodedata


# ============================================================
# COMMANDS
# ============================================================

COMMANDS = {
    "LIGHT_ON": (
        "bật đèn",
        "mở đèn",
        "bật cái đèn",
        "mở cái đèn",
        "bật điện",
        "mở điện",
        "cho đèn sáng",
    ),

    "LIGHT_OFF": (
        "tắt đèn",
        "đóng đèn",
        "tắt cái đèn",
        "đóng cái đèn",
        "tắt điện",
        "cho đèn tắt",
    ),

    "FAN_ON": (
        "bật quạt",
        "mở quạt",
        "bật cái quạt",
        "mở cái quạt",
        "cho quạt chạy",
    ),

    "FAN_OFF": (
        "tắt quạt",
        "đóng quạt",
        "tắt cái quạt",
        "đóng cái quạt",
        "dừng quạt",
        "cho quạt dừng",
    ),
}


def normalize(text: str) -> str:
    """Chuẩn hóa text để dễ nhận diện dù ASR sai dấu."""

    text = text.lower()

    # Bỏ dấu câu
    text = re.sub(r"[^\w\s]", " ", text)

    # đ -> d
    text = text.replace("đ", "d")

    # Bỏ dấu tiếng Việt
    text = "".join(
        c
        for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )

    # Chuẩn hóa khoảng trắng
    return re.sub(r"\s+", " ", text).strip()


def classify_command(text: str) -> str:
    """Nhận diện lệnh từ câu nói."""

    text = normalize(text)

    for command, phrases in COMMANDS.items():
        for phrase in phrases:
            if normalize(phrase) in text:
                return command

    return "UNKNOWN"


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    tests = (
        "BẬT ĐÈN",
        "bat den",
        "bật cái đèn",
        "mo den",
        "cho den sang",

        "TẮT ĐÈN",
        "tat dien",

        "BẬT QUẠT",
        "mo quat",
        "cho quat chay",

        "TẮT QUẠT",
        "dung quat",

        "chúc mừng sinh nhật",
        "mở cửa",
    )

    for text in tests:
        print(f"{text:25} -> {classify_command(text)}")
