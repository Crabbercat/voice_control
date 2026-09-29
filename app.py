from pathlib import Path
import tempfile

import av
import librosa
import numpy as np
import torch

from flask import Flask, jsonify, render_template, request
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor

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

CERT_DIR = BASE_DIR / "certs"

CERT_FILE = CERT_DIR / "server.crt"
KEY_FILE = CERT_DIR / "server.key"

SAMPLE_RATE = 16_000

HOST = "0.0.0.0"
PORT = 5000


# ============================================================
# CHECK FILES
# ============================================================

if not MODEL_DIR.is_dir():
    raise FileNotFoundError(
        f"Local model not found: {MODEL_DIR}\n"
        "Please run download_model.py first."
    )

if not CERT_FILE.is_file():
    raise FileNotFoundError(
        f"SSL certificate not found: {CERT_FILE}"
    )

if not KEY_FILE.is_file():
    raise FileNotFoundError(
        f"SSL private key not found: {KEY_FILE}"
    )


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)


# ============================================================
# DEVICE
# ============================================================

device = torch.device(
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)


# ============================================================
# STARTUP LOG
# ============================================================

print("=" * 60)
print("[INFO] Voice Control HTTPS Server")
print("=" * 60)

print(f"[INFO] Base directory : {BASE_DIR}")
print(f"[INFO] Model directory: {MODEL_DIR}")
print(f"[INFO] Device         : {device}")
print(f"[INFO] Sample rate    : {SAMPLE_RATE} Hz")

print(f"[INFO] Certificate    : {CERT_FILE}")
print(f"[INFO] Private key    : {KEY_FILE}")

print(f"[INFO] HTTPS host     : {HOST}")
print(f"[INFO] HTTPS port     : {PORT}")

print("=" * 60)


# ============================================================
# LOAD PROCESSOR
# ============================================================

print("[INFO] Loading Wav2Vec2 processor...")

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
    """
    Decode browser-recorded audio.

    Input:
        WebM / OGG / OPUS

    Output:
        mono
        16 kHz
        float32
    """

    chunks = []

    resampler = av.audio.resampler.AudioResampler(
        format="s16",
        layout="mono",
        rate=SAMPLE_RATE,
    )

    print(
        f"[INFO] Decoding audio: "
        f"{audio_path.name}"
    )

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

        # Flush resampler
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
            "The uploaded audio contains no samples."
        )

    audio = np.concatenate(chunks)

    # int16 -> float32
    audio = (
        audio.astype(np.float32)
        / 32768.0
    )

    duration = (
        len(audio)
        / SAMPLE_RATE
    )

    print(
        f"[INFO] Audio loaded: "
        f"{len(audio)} samples "
        f"({duration:.2f}s)"
    )

    return audio


# ============================================================
# SPEECH TO TEXT
# ============================================================

def transcribe_audio(audio_path: Path) -> str:
    """
    Convert audio into Vietnamese text.
    """

    suffix = audio_path.suffix.lower()

    print("=" * 60)
    print("[INFO] Starting transcription")
    print(f"[INFO] File format: {suffix}")

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
    # Normal audio
    # --------------------------------------------------------

    else:

        audio, _ = librosa.load(
            audio_path,
            sr=SAMPLE_RATE,
            mono=True,
        )

        print(
            f"[INFO] Audio loaded with librosa: "
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

    print(
        f"[INFO] Recognized text: "
        f"{text}"
    )

    return text


# ============================================================
# WEB PAGE
# ============================================================

@app.get("/")
def index():

    return render_template(
        "index.html"
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    return jsonify(
        success=True,
        status="running",
        protocol="https",
        device=str(device),
        model=str(MODEL_DIR),
    )


# ============================================================
# RECOGNIZE AUDIO
# ============================================================

@app.post("/recognize")
def recognize():

    print("\n")
    print("=" * 60)
    print("[REQUEST] POST /recognize")
    print("=" * 60)

    # --------------------------------------------------------
    # Get audio
    # --------------------------------------------------------

    audio_file = request.files.get(
        "audio"
    )

    if audio_file is None:

        print(
            "[ERROR] No audio file provided."
        )

        return jsonify(
            success=False,
            error="No audio file provided.",
        ), 400

    if not audio_file.filename:

        print(
            "[ERROR] Audio filename is empty."
        )

        return jsonify(
            success=False,
            error="Audio filename is empty.",
        ), 400

    print(
        f"[INFO] Uploaded file: "
        f"{audio_file.filename}"
    )

    # --------------------------------------------------------
    # File extension
    # --------------------------------------------------------

    suffix = Path(
        audio_file.filename
    ).suffix.lower()

    if not suffix:
        suffix = ".webm"

    print(
        f"[INFO] Audio suffix: {suffix}"
    )

    temporary_path = None

    try:

        # ----------------------------------------------------
        # Save temporary file
        # ----------------------------------------------------

        with tempfile.NamedTemporaryFile(
            suffix=suffix,
            delete=False,
        ) as temporary_file:

            audio_file.save(
                temporary_file
            )

            temporary_path = Path(
                temporary_file.name
            )

        print(
            f"[INFO] Temporary file: "
            f"{temporary_path}"
        )

        # ----------------------------------------------------
        # Speech recognition
        # ----------------------------------------------------

        text = transcribe_audio(
            temporary_path
        )

        # ----------------------------------------------------
        # Classify command
        # ----------------------------------------------------

        command = classify_command(
            text
        )

        print(
            f"[INFO] Command: {command}"
        )

        # ----------------------------------------------------
        # Hardware
        # ----------------------------------------------------

        hardware_result = (
            hardware_controller.execute(
                command
            )
        )

        print(
            f"[INFO] Hardware: "
            f"{hardware_result}"
        )

        # ----------------------------------------------------
        # Response
        # ----------------------------------------------------

        return jsonify(
            success=True,
            text=text,
            command=command,
            hardware=hardware_result,
        )

    except Exception as error:

        app.logger.exception(
            "Audio recognition failed"
        )

        print(
            f"[ERROR] "
            f"{type(error).__name__}: "
            f"{error}"
        )

        return jsonify(
            success=False,
            error=str(error),
        ), 500

    finally:

        # ----------------------------------------------------
        # Cleanup
        # ----------------------------------------------------

        if temporary_path is not None:

            try:

                temporary_path.unlink(
                    missing_ok=True
                )

                print(
                    "[INFO] Temporary file "
                    "removed."
                )

            except Exception as cleanup_error:

                print(
                    "[WARNING] Failed to remove "
                    f"temporary file: "
                    f"{cleanup_error}"
                )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("[INFO] Starting HTTPS Flask server")
    print("=" * 60)

    print(
        f"[INFO] HTTPS URL:"
        f" https://0.0.0.0:{PORT}"
    )

    print(
        "[INFO] Access from another computer using:"
    )

    print(
        f"       https://<RASPBERRY_PI_IP>:{PORT}"
    )

    print("=" * 60)
    print()

    app.run(
        host=HOST,
        port=PORT,
        debug=False,
        ssl_context=(
            str(CERT_FILE),
            str(KEY_FILE),
        ),
    )