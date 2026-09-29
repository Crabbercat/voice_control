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


BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "models" / "wav2vec2-vietnamese-160h"
SAMPLE_RATE = 16_000

if not MODEL_DIR.is_dir():
    raise FileNotFoundError(
        f"Local model not found: {MODEL_DIR}. Run download_model.py first."
    )

app = Flask(__name__)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"[INFO] Using device: {device}")
print(f"[INFO] Model: {MODEL_DIR}")

processor = Wav2Vec2Processor.from_pretrained(
    MODEL_DIR,
    local_files_only=True,
)
model = Wav2Vec2ForCTC.from_pretrained(
    MODEL_DIR,
    local_files_only=True,
)
model.to(device)
model.eval()


def transcribe_audio(audio_path: Path) -> str:
    if audio_path.suffix.lower() in {".webm", ".ogg", ".opus"}:
        audio = load_browser_audio(audio_path)
    else:
        audio, _ = librosa.load(audio_path, sr=SAMPLE_RATE, mono=True)

    inputs = processor(
        audio,
        sampling_rate=SAMPLE_RATE,
        return_tensors="pt",
    )

    with torch.inference_mode():
        logits = model(inputs.input_values.to(device)).logits

    predicted_ids = torch.argmax(logits, dim=-1)
    return processor.batch_decode(predicted_ids)[0].strip()


def load_browser_audio(audio_path: Path) -> np.ndarray:
    chunks = []
    resampler = av.audio.resampler.AudioResampler(
        format="s16",
        layout="mono",
        rate=SAMPLE_RATE,
    )

    with av.open(str(audio_path)) as container:
        for frame in container.decode(audio=0):
            for resampled_frame in resampler.resample(frame):
                chunks.append(resampled_frame.to_ndarray().reshape(-1))

        for resampled_frame in resampler.resample(None):
            chunks.append(resampled_frame.to_ndarray().reshape(-1))

    if not chunks:
        raise ValueError("The uploaded audio contains no samples.")

    return np.concatenate(chunks).astype(np.float32) / 32768.0


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/recognize")
def recognize():
    audio_file = request.files.get("audio")
    if audio_file is None or not audio_file.filename:
        return jsonify(success=False, error="No audio file provided"), 400

    suffix = Path(audio_file.filename).suffix or ".webm"
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temporary_file:
            audio_file.save(temporary_file)
            temporary_path = Path(temporary_file.name)

        text = transcribe_audio(temporary_path)
        command = classify_command(text)
        hardware = hardware_controller.execute(command)
        return jsonify(success=True, text=text, command=command, hardware=hardware)
    except Exception as error:
        app.logger.exception("Audio recognition failed")
        return jsonify(success=False, error=str(error)), 500
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

