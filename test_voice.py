from pathlib import Path

import torch
import librosa

from transformers import (
    Wav2Vec2Processor,
    Wav2Vec2ForCTC
)


# ============================================================
# CONFIG
# ============================================================

MODEL_DIR = Path("models/wav2vec2-vietnamese-160h")
VOICE_DIR = Path("voice")

SAMPLE_RATE = 16000

# Các cách nói mà ta chấp nhận là "bật đèn"
LIGHT_ON_KEYWORDS = [
    "bật đèn",
    "bat den",
    "mở đèn",
    "mo den",
    "cho đèn sáng",
    "cho den sang",
]


# ============================================================
# DEVICE
# ============================================================

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("=" * 60)
print("Vietnamese Voice Command Test")
print("=" * 60)

print(f"Device: {device}")
print(f"Model:  {MODEL_DIR}")
print(f"Voice:  {VOICE_DIR}")


# ============================================================
# CHECK
# ============================================================

if not MODEL_DIR.exists():
    raise FileNotFoundError(
        f"Model not found: {MODEL_DIR}\n"
        "Run download_model.py first."
    )

if not VOICE_DIR.exists():
    raise FileNotFoundError(
        f"Voice directory not found: {VOICE_DIR}"
    )


# ============================================================
# LOAD MODEL
# ============================================================

print("\nLoading processor...")

processor = Wav2Vec2Processor.from_pretrained(
    MODEL_DIR,
    local_files_only=True
)

print("Loading model...")

model = Wav2Vec2ForCTC.from_pretrained(
    MODEL_DIR,
    local_files_only=True
)

model.to(device)
model.eval()

print("Model loaded successfully.")


# ============================================================
# NORMALIZE TEXT
# ============================================================

def normalize_text(text: str) -> str:
    """
    Normalize transcript for keyword matching.
    """

    text = text.lower().strip()

    # Collapse multiple spaces
    text = " ".join(text.split())

    return text


# ============================================================
# CHECK LIGHT ON
# ============================================================

def is_light_on_command(text: str) -> bool:

    text = normalize_text(text)

    for keyword in LIGHT_ON_KEYWORDS:

        if keyword in text:
            return True

    return False


# ============================================================
# TRANSCRIBE
# ============================================================

def transcribe(audio_path: Path) -> str:

    # Load audio and force 16 kHz mono
    audio, sample_rate = librosa.load(
        audio_path,
        sr=SAMPLE_RATE,
        mono=True
    )

    # Processor
    inputs = processor(
        audio,
        sampling_rate=SAMPLE_RATE,
        return_tensors="pt"
    )

    input_values = inputs.input_values.to(device)

    # Inference
    with torch.no_grad():

        logits = model(
            input_values
        ).logits

    # Best token for each timestep
    predicted_ids = torch.argmax(
        logits,
        dim=-1
    )

    # Decode
    text = processor.batch_decode(
        predicted_ids
    )[0]

    return text


# ============================================================
# FIND AUDIO FILES
# ============================================================

audio_extensions = {
    ".wav",
    ".mp3",
    ".flac",
    ".ogg",
    ".m4a"
}

audio_files = sorted(
    [
        path
        for path in VOICE_DIR.iterdir()
        if path.is_file()
        and path.suffix.lower() in audio_extensions
    ]
)


if not audio_files:

    print("\nNo audio files found.")

    raise SystemExit(0)


# ============================================================
# TEST
# ============================================================

print("\n")
print("=" * 60)
print(f"Found {len(audio_files)} audio files")
print("=" * 60)


correct = 0


for index, audio_path in enumerate(audio_files, start=1):

    print()
    print(
        f"[{index}/{len(audio_files)}] "
        f"{audio_path.name}"
    )

    try:

        text = transcribe(audio_path)

        text_normalized = normalize_text(text)

        matched = is_light_on_command(
            text_normalized
        )

        if matched:

            correct += 1

            print("  Transcript :", text)
            print("  Command    : LIGHT_ON")
            print("  Result     : PASS")

        else:

            print("  Transcript :", text)
            print("  Command    : UNKNOWN")
            print("  Result     : FAIL")

    except Exception as e:

        print("  ERROR:", e)


# ============================================================
# SUMMARY
# ============================================================

total = len(audio_files)

accuracy = (
    correct / total * 100
    if total > 0
    else 0
)


print()
print("=" * 60)
print("SUMMARY")
print("=" * 60)

print(f"Total files : {total}")
print(f"Detected    : {correct}")
print(f"Not detected: {total - correct}")
print(f"Accuracy    : {accuracy:.2f}%")

print("=" * 60)