from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher


# ============================================================
# COMMANDS
# ============================================================

SIMILARITY_THRESHOLD = 0.9

COMMANDS = {
    "ALL_ON": (
        "bật hết",
        "mở hết",
        "bật tất cả",
        "mở tất cả",
        "bật toàn bộ",
        "mở toàn bộ",
    ),

    "ALL_OFF": (
        "tắt hết",
        "đóng hết",
        "tắt tất cả",
        "dừng tất cả",
        "tắt toàn bộ",
        "dừng toàn bộ",
    ),

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
            normalized_phrase = normalize(phrase)
            if normalized_phrase in text:
                return command

    best_command = "UNKNOWN"
    best_similarity = 0.0

    for command, phrases in COMMANDS.items():
        for phrase in phrases:
            normalized_phrase = normalize(phrase)
            phrase_words = normalized_phrase.split()
            text_words = text.split()
            window_sizes = range(
                max(1, len(phrase_words) - 1),
                min(len(text_words), len(phrase_words) + 1) + 1,
            )
            for window_size in window_sizes:
                for start in range(len(text_words) - window_size + 1):
                    candidate = " ".join(
                        text_words[start:start + window_size]
                    )
                    similarity = SequenceMatcher(
                        None,
                        normalized_phrase,
                        candidate,
                    ).ratio()
                    if similarity >= SIMILARITY_THRESHOLD and similarity > best_similarity:
                        best_command = command
                        best_similarity = similarity

    return best_command


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

        "bật hết",
        "tat tat ca",

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
