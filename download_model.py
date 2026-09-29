from pathlib import Path

from transformers import (
    Wav2Vec2Processor,
    Wav2Vec2ForCTC
)


MODEL_NAME = "khanhld/wav2vec2-base-vietnamese-160h"
MODEL_DIR = Path("models/wav2vec2-vietnamese-160h")


def main():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Downloading Vietnamese Wav2Vec2 model")
    print("=" * 60)

    print(f"Model: {MODEL_NAME}")
    print(f"Local directory: {MODEL_DIR}")

    print("\n[1/2] Downloading processor...")

    processor = Wav2Vec2Processor.from_pretrained(
        MODEL_NAME
    )

    processor.save_pretrained(MODEL_DIR)

    print("Processor saved.")

    print("\n[2/2] Downloading model...")

    model = Wav2Vec2ForCTC.from_pretrained(
        MODEL_NAME
    )

    model.save_pretrained(MODEL_DIR)

    print("Model saved.")

    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)
    print(f"Everything is stored in: {MODEL_DIR}")


if __name__ == "__main__":
    main()