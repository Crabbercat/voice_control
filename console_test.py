from pathlib import Path

import av
import librosa
import numpy as np
import torch

from transformers import (
    Wav2Vec2ForCTC,
    Wav2Vec2Processor,
)

from command_classifier import classify_command
from hardware_controller import hardware_controller


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

MODEL_DIR = (
    BASE_DIR
    / "models"
    / "wav2vec2-vietnamese-160h"
)

SAMPLE_RATE = 16_000


# ============================================================
# CHECK MODEL
# ============================================================

if not MODEL_DIR.is_dir():
    raise FileNotFoundError(
        f"Model not found: {MODEL_DIR}"
    )


# ============================================================
# DEVICE
# ============================================================

device = torch.device(
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)


# ============================================================
# STARTUP
# ============================================================

print("=" * 60)
print("VOICE CONTROL - CONSOLE MODE")
print("=" * 60)

print(f"[INFO] Model : {MODEL_DIR}")
print(f"[INFO] Device: {device}")
print(f"[INFO] Rate  : {SAMPLE_RATE} Hz")

print("=" * 60)


# ============================================================
# LOAD PROCESSOR
# ============================================================

print("[INFO] Loading processor...")

processor = Wav2Vec2Processor.from_pretrained(
    MODEL_DIR,
    local_files_only=True,
)

print("[INFO] Processor loaded.")


# ============================================================
# LOAD MODEL
# ============================================================

print("[INFO] Loading Wav2Vec2 model...")

model = Wav2Vec2ForCTC.from_pretrained(
    MODEL_DIR,
    local_files_only=True,
)

model.to(device)
model.eval()

print("[INFO] Model loaded successfully.")
print("=" * 60)


# ============================================================
# AUDIO LOADER
# ============================================================

def load_browser_audio(audio_path: Path) -> np.ndarray:

    chunks = []

    resampler = av.audio.resampler.AudioResampler(
        format="s16",
        layout="mono",
        rate=SAMPLE_RATE,
    )

    print(f"[INFO] Decoding: {audio_path.name}")

    with av.open(str(audio_path)) as container:

        for frame in container.decode(audio=0):

            resampled_frames = (
                resampler.resample(frame)
            )

            for resampled_frame in resampled_frames:

                audio_array = (
                    resampled_frame
                    .to_ndarray()
                    .reshape(-1)
                )

                chunks.append(audio_array)

        # Flush remaining samples
        remaining_frames = (
            resampler.resample(None)
        )

        for resampled_frame in remaining_frames:

            audio_array = (
                resampled_frame
                .to_ndarray()
                .reshape(-1)
            )

            chunks.append(audio_array)

    if not chunks:
        raise ValueError(
            "Audio contains no samples."
        )

    audio = np.concatenate(chunks)

    # int16 -> float32
    audio = (
        audio.astype(np.float32)
        / 32768.0
    )

    duration = len(audio) / SAMPLE_RATE

    print(
        f"[INFO] Audio: "
        f"{len(audio)} samples "
        f"({duration:.2f}s)"
    )

    return audio


# ============================================================
# SPEECH TO TEXT
# ============================================================

def transcribe_audio(audio_path: Path) -> str:

    suffix = audio_path.suffix.lower()

    print("=" * 60)
    print("[INFO] Starting transcription")
    print(f"[INFO] Format: {suffix}")

    # --------------------------------------------------------
    # Browser audio
    # --------------------------------------------------------

    if suffix in {
        ".webm",
        ".ogg",
        ".opus",
    }:

        audio = load_browser_audio(
            audio_path
        )

    # --------------------------------------------------------
    # WAV / MP3 / other audio
    # --------------------------------------------------------

    else:

        print("[INFO] Loading audio with librosa...")

        audio, _ = librosa.load(
            audio_path,
            sr=SAMPLE_RATE,
            mono=True,
        )

        print(
            f"[INFO] Audio loaded: "
            f"{len(audio)} samples"
        )

    # --------------------------------------------------------
    # Processor
    # --------------------------------------------------------

    inputs = processor(
        audio,
        sampling_rate=SAMPLE_RATE,
        return_tensors="pt",
    )

    input_values = (
        inputs.input_values.to(device)
    )

    # --------------------------------------------------------
    # Model inference
    # --------------------------------------------------------

    print("[INFO] Running Wav2Vec2...")

    with torch.inference_mode():

        logits = model(
            input_values
        ).logits

    # --------------------------------------------------------
    # Decode
    # --------------------------------------------------------

    predicted_ids = torch.argmax(
        logits,
        dim=-1,
    )

    text = processor.batch_decode(
        predicted_ids
    )[0].strip()

    print(f"[INFO] Text: {text}")

    return text


# ============================================================
# PROCESS COMMAND
# ============================================================

def process_audio(audio_path: Path):

    print("\n")
    print("=" * 60)
    print("PROCESSING")
    print("=" * 60)

    # --------------------------------------------------------
    # Speech-to-Text
    # --------------------------------------------------------

    text = transcribe_audio(
        audio_path
    )

    # --------------------------------------------------------
    # Command Classification
    # --------------------------------------------------------

    print("[INFO] Classifying command...")

    command = classify_command(text)

    print(
        f"[INFO] Command: {command}"
    )

    # --------------------------------------------------------
    # Hardware
    # --------------------------------------------------------

    print("[INFO] Executing hardware command...")

    hardware_result = (
        hardware_controller.execute(
            command
        )
    )

    hardware_result.update(
        hardware_controller.status()
    )

    # --------------------------------------------------------
    # Result
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("RESULT")
    print("=" * 60)

    print(f"Recognized text : {text}")
    print(f"Command         : {command}")
    print(f"Hardware        : {hardware_result}")

    print("=" * 60)


# ============================================================
# MAIN CONSOLE
# ============================================================

def main():

    print()
    print("Enter path to an audio file.")
    print("Supported: WAV, MP3, WebM, OGG, OPUS")
    print("Type 'exit' to quit.")
    print()

    while True:

        audio_input = input(
            "Audio file > "
        ).strip()

        if audio_input.lower() == "exit":
            print("[INFO] Exiting...")
            break

        if not audio_input:
            continue

        audio_path = Path(audio_input)

        if not audio_path.is_file():

            print(
                f"[ERROR] File not found: "
                f"{audio_path}"
            )

            continue

        try:

            process_audio(
                audio_path
            )

        except Exception as error:

            print()
            print(
                f"[ERROR] "
                f"{type(error).__name__}: {error}"
            )

        print()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()