# Voice Recognition Web Demo - Specification

## 1. Goal

Build a minimal local web application for testing Vietnamese speech recognition
using the already downloaded local model:

`models/wav2vec2-vietnamese-160h/`

The user should be able to:

1. Open the web page.
2. Press **Record** to start recording from the browser microphone.
3. Speak Vietnamese.
4. Press **Stop** to finish recording.
5. Browser sends the recorded audio to the Python backend.
6. Backend runs the local Wav2Vec2 Vietnamese model.
7. Backend returns the recognized text.
8. Web page displays the recognized text.

Do **not** implement GPIO, Raspberry Pi control, authentication, database,
user accounts, or unnecessary features.

---

## 2. Technology

### Backend

- Python
- Flask
- PyTorch
- Transformers
- Librosa
- SoundFile

### Frontend

- HTML
- CSS
- Vanilla JavaScript
- Browser MediaRecorder API

The application must use the existing local model.

**Do not download the model again when starting the application.**

---

## 3. Project Structure

```text
voice_iot/
├── models/
│   └── wav2vec2-vietnamese-160h/
│
├── voice/
│
├── templates/
│   └── index.html
│
├── app.py
├── requirements.txt
└── SPEC.md
```

---

## 4. Backend

Create `app.py`.

Use Flask.

Load the model once when the application starts:

```text
models/wav2vec2-vietnamese-160h/
```

Use:

```python
Wav2Vec2Processor.from_pretrained(
    MODEL_DIR,
    local_files_only=True
)

Wav2Vec2ForCTC.from_pretrained(
    MODEL_DIR,
    local_files_only=True
)
```

The model must **not** be loaded for every request.

Use GPU if CUDA is available, otherwise use CPU.

### Recognition flow

```text
POST /recognize
        ↓
receive audio file
        ↓
convert audio to:
- mono
- 16 kHz
        ↓
Wav2Vec2 inference
        ↓
decode transcript
        ↓
return JSON
```

### Success response

```json
{
    "success": true,
    "text": "bật đèn"
}
```

### Error response

```json
{
    "success": false,
    "error": "error message"
}
```

---

## 5. Audio Upload

The frontend sends the recorded audio using:

```text
POST /recognize
```

Use:

```text
multipart/form-data
```

Field name:

```text
audio
```

The backend should process the uploaded audio temporarily.

Do not permanently save recordings unless necessary.

---

## 6. Frontend

Create:

```text
templates/index.html
```

Keep the UI extremely simple.

Example:

```text
+----------------------------------+
|     Vietnamese Voice Test        |
|                                  |
|          [ Record ]              |
|                                  |
| Status: Ready                    |
|                                  |
| Recognized text:                 |
| "bật đèn"                        |
+----------------------------------+
```

### Record button

Initial state:

```text
Record
```

When clicked:

- Request microphone permission.
- Start `MediaRecorder`.
- Change button text to `Stop`.
- Change status to `Recording...`.

### Stop button

When clicked:

- Stop `MediaRecorder`.
- Create an audio Blob.
- Send the audio to `/recognize`.
- Change status to `Processing...`.

After receiving the response:

```text
Recognized text:
bật đèn
```

---

## 7. JavaScript

Use the browser's native APIs:

```javascript
navigator.mediaDevices.getUserMedia({
    audio: true
})
```

and:

```javascript
new MediaRecorder(stream)
```

Do not use:

- React
- Vue
- Bootstrap
- Tailwind
- Other frontend frameworks

Keep the frontend implementation inside one `index.html`.

---

## 8. UX

Required states:

```text
Ready
Recording...
Processing...
Recognized: <text>
Error: <message>
```

Disable the button while the backend is processing.

After processing finishes, allow recording again.

---

## 9. Run

Create `requirements.txt` containing all required Python dependencies.

Expected startup:

```bash
pip install -r requirements.txt
python app.py
```

The server should listen on:

```text
http://127.0.0.1:5000
```

Opening this address should show the web interface.

---

## 10. Important Constraints

- Use the existing local model.
- Do not call Hugging Face during runtime.
- Do not download models automatically.
- Do not implement Raspberry Pi GPIO yet.
- Do not implement command classification yet.
- Do not implement authentication.
- Do not implement a database.
- Do not over-engineer the project.
- Keep the implementation easy to understand and modify later.

---

## 11. Future Extension

The current project only performs:

```text
Microphone
    ↓
Web Browser
    ↓
Audio Upload
    ↓
Wav2Vec2
    ↓
Vietnamese Text
```

Later it will be extended to:

```text
Vietnamese Text
    ↓
Command Parser
    ↓
LIGHT_ON
LIGHT_OFF
MOTOR_FORWARD
MOTOR_BACKWARD
MOTOR_STOP
    ↓
Raspberry Pi GPIO
```

Do **not** implement this future functionality now.
