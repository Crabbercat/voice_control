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

SAMPLE_RATE = 16_000

HOST = "0.0.0.0"
PORT = 5000


# ============================================================
# CHECK MODEL
# ============================================================

if not MODEL_DIR.is_dir():
    raise FileNotFoundError(
        f"Local model not found: {MODEL_DIR}\n"
        "Please run download_model.py first."
    )


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)


# ============================================================
# LOAD DEVICE
# ============================================================

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("=" * 60)
print("[INFO] Voice Control Server")
print("=" * 60)
print(f"[INFO] Base directory : {BASE_DIR}")
print(f"[INFO] Model directory: {MODEL_DIR}")
print(f"[INFO] Device         : {device}")
print(f"[INFO] Sample rate    : {SAMPLE_RATE} Hz")
print("=" * 60)


# ============================================================
# LOAD WAV2VEC2 PROCESSOR
# ============================================================

print("[INFO] Loading processor...")

processor = Wav2Vec2Processor.from_pretrained(
    MODEL_DIR,
    local_files_only=True,
)

print("[INFO] Processor loaded.")


# ============================================================
# LOAD WAV2VEC2 MODEL
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
# AUDIO PROCESSING
# ============================================================

def load_browser_audio(audio_path: Path) -> np.ndarray:
    """
    Load audio recorded by browser.

    Browser usually sends:
        WebM / OGG / OPUS

    Audio is converted to:
        - mono
        - 16 kHz
        - float32
        - range approximately [-1, 1]
    """

    chunks = []

    resampler = av.audio.resampler.AudioResampler(
        format="s16",
        layout="mono",
        rate=SAMPLE_RATE,
    )

    print(f"[INFO] Decoding audio: {audio_path.name}")

    with av.open(str(audio_path)) as container:

        for frame in container.decode(audio=0):

            resampled_frames = resampler.resample(frame)

            for resampled_frame in resampled_frames:
                audio_array = (
                    resampled_frame
                    .to_ndarray()
                    .reshape(-1)
                )

                chunks.append(audio_array)

        # Flush remaining samples from resampler
        remaining_frames = resampler.resample(None)

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
    audio = audio.astype(np.float32) / 32768.0

    print(
        f"[INFO] Audio loaded: "
        f"{len(audio)} samples "
        f"({len(audio) / SAMPLE_RATE:.2f}s)"
    )

    return audio


def transcribe_audio(audio_path: Path) -> str:
    """
    Convert an audio file into Vietnamese text
    using the local Wav2Vec2 model.
    """

    suffix = audio_path.suffix.lower()

    print(f"[INFO] Transcribing: {audio_path.name}")
    print(f"[INFO] Audio format: {suffix}")

    # --------------------------------------------------------
    # Browser audio
    # --------------------------------------------------------

    if suffix in {".webm", ".ogg", ".opus"}:

        audio = load_browser_audio(audio_path)

    # --------------------------------------------------------
    # Normal audio files
    # --------------------------------------------------------

    else:

        audio, _ = librosa.load(
            audio_path,
            sr=SAMPLE_RATE,
            mono=True,
        )

        print(
            f"[INFO] Audio loaded with librosa: "
            f"{len(audio)} samples "
            f"({len(audio) / SAMPLE_RATE:.2f}s)"
        )

    # --------------------------------------------------------
    # Prepare input for Wav2Vec2
    # --------------------------------------------------------

    inputs = processor(
        audio,
        sampling_rate=SAMPLE_RATE,
        return_tensors="pt",
    )

    input_values = inputs.input_values.to(device)

    # --------------------------------------------------------
    # Inference
    # --------------------------------------------------------

    print("[INFO] Running Wav2Vec2 inference...")

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

    print(f"[INFO] Recognized text: {text}")

    return text


# ============================================================
# ROUTES
# ============================================================

@app.get("/")
def index():
    """
    Render the voice-control web interface.
    """

    return render_template("index.html")


@app.post("/recognize")
def recognize():
    """
    Receive recorded audio from browser.

    Request:
        multipart/form-data
        audio=<audio file>

    Response:
        {
            "success": true,
            "text": "...",
            "command": "LIGHT_ON",
            "hardware": {...}
        }
    """

    print("\n" + "=" * 60)
    print("[REQUEST] POST /recognize")
    print("=" * 60)

    # --------------------------------------------------------
    # Get uploaded audio
    # --------------------------------------------------------

    audio_file = request.files.get("audio")

    if audio_file is None:
        print("[ERROR] No audio field in request.")

        return jsonify(
            success=False,
            error="No audio file provided.",
        ), 400

    if not audio_file.filename:
        print("[ERROR] Audio filename is empty.")

        return jsonify(
            success=False,
            error="Audio filename is empty.",
        ), 400

    print(f"[INFO] Uploaded file: {audio_file.filename}")

    # --------------------------------------------------------
    # Determine file extension
    # --------------------------------------------------------

    suffix = Path(
        audio_file.filename
    ).suffix.lower()

    if not suffix:
        suffix = ".webm"

    print(f"[INFO] File suffix: {suffix}")

    temporary_path = None

    try:

        # ----------------------------------------------------
        # Save temporary audio file
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
        # Speech-to-text
        # ----------------------------------------------------

        text = transcribe_audio(
            temporary_path
        )

        # ----------------------------------------------------
        # Command classification
        # ----------------------------------------------------

        command = classify_command(
            text
        )

        print(
            f"[INFO] Classified command: "
            f"{command}"
        )

        # ----------------------------------------------------
        # Hardware control
        # ----------------------------------------------------

        hardware_result = (
            hardware_controller.execute(
                command
            )
        )

        print(
            f"[INFO] Hardware result: "
            f"{hardware_result}"
        )

        # ----------------------------------------------------
        # Response
        # ----------------------------------------------------

        response = {
            "success": True,
            "text": text,
            "command": command,
            "hardware": hardware_result,
        }

        print(
            f"[INFO] Response: {response}"
        )

        return jsonify(response), 200

    except Exception as error:

        # ----------------------------------------------------
        # Error logging
        # ----------------------------------------------------

        app.logger.exception(
            "Audio recognition failed"
        )

        print(
            f"[ERROR] {type(error).__name__}: "
            f"{error}"
        )

        return jsonify(
            success=False,
            error=str(error),
        ), 500

    finally:

        # ----------------------------------------------------
        # Remove temporary file
        # ----------------------------------------------------

        if temporary_path is not None:

            try:

                temporary_path.unlink(
                    missing_ok=True
                )

                print(
                    f"[INFO] Removed temporary file: "
                    f"{temporary_path}"
                )

            except Exception as cleanup_error:

                print(
                    "[WARNING] Could not remove "
                    f"temporary file: {cleanup_error}"
                )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    """
    Simple server health check.
    """

    return jsonify(
        success=True,
        status="running",
        device=str(device),
        model=str(MODEL_DIR),
    ), 200


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("[INFO] Starting Flask server...")
    print(f"[INFO] Host: {HOST}")
    print(f"[INFO] Port: {PORT}")
    print("=" * 60)
    print()

    app.run(
        host=HOST,
        port=PORT,
        debug=False,
    )