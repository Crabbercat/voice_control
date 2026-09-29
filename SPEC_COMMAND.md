# Voice Recognition + IoT Command Classification - Specification

## 1. Goal

Extend the existing Vietnamese voice recognition web demo.

The existing system already performs:

```text
Microphone
    ↓
Web Browser
    ↓
Audio Upload
    ↓
Local Wav2Vec2
    ↓
Vietnamese Text
```

Add a simple command classification layer:

```text
Vietnamese Text
    ↓
Command Classifier
    ↓
IoT Action
```

Supported actions:

```text
LIGHT_ON
LIGHT_OFF
FAN_ON
FAN_OFF
UNKNOWN
```

Do not implement GPIO or Raspberry Pi control yet.

---

## 2. Existing Model

Use the already downloaded local model:

```text
models/wav2vec2-vietnamese-160h/
```

The application must continue to use:

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

Do not download the model at runtime.

Do not change the existing speech-to-text implementation unless necessary.

---

## 3. Command Classification

Create:

```text
command_classifier.py
```

This module converts recognized Vietnamese text into one of the supported
commands.

### Supported commands

| Command | Example phrases |
|---|---|
| `LIGHT_ON` | "bật đèn", "mở đèn", "bật cái đèn", "cho đèn sáng" |
| `LIGHT_OFF` | "tắt đèn", "đóng đèn", "tắt cái đèn", "cho đèn tắt" |
| `FAN_ON` | "bật quạt", "mở quạt", "bật cái quạt", "cho quạt chạy" |
| `FAN_OFF` | "tắt quạt", "đóng quạt", "tắt cái quạt", "dừng quạt" |
| `UNKNOWN` | Any text that does not match a supported command |

The implementation can use simple phrase matching.

Do not use another AI/NLP model for this stage.

---

## 4. Text Normalization

Before classification:

- Convert text to lowercase.
- Remove unnecessary repeated spaces.
- Trim leading/trailing spaces.
- Keep Vietnamese diacritics.

Example:

```text
"BẬT   ĐÈN"
        ↓
"bật đèn"
```

The classifier should return:

```text
LIGHT_ON
```

---

## 5. Classification Function

`command_classifier.py` should expose:

```python
def classify_command(text: str) -> str:
    ...
```

Examples:

```python
classify_command("bật đèn")
# LIGHT_ON

classify_command("mở cái quạt")
# FAN_ON

classify_command("chúc mừng sinh nhật")
# UNKNOWN
```

The module should also be directly executable for local testing:

```bash
python command_classifier.py
```

It should print several example inputs and detected commands.

---

## 6. Backend Integration

Modify `app.py`.

After Wav2Vec2 generates the transcript:

```text
audio
 ↓
Wav2Vec2
 ↓
text
```

call:

```python
command = classify_command(text)
```

The `/recognize` endpoint should return:

```json
{
    "success": true,
    "text": "bật đèn phòng khách",
    "command": "LIGHT_ON"
}
```

For an unrelated sentence:

```json
{
    "success": true,
    "text": "chúc mừng sinh nhật",
    "command": "UNKNOWN"
}
```

`UNKNOWN` is a valid classification result, not an API error.

---

## 7. Frontend

Keep the existing simple interface.

Add an `ACTION` section below the recognized text.

Example:

```text
LOCAL WAV2VEC2 TEST

Vietnamese Voice Test

[ Record ]

Status: Recognized

RECOGNIZED TEXT

bật đèn phòng khách

ACTION

LIGHT_ON
```

For an unknown sentence:

```text
RECOGNIZED TEXT

chúc mừng sinh nhật

ACTION

UNKNOWN
```

Continue using:

- HTML
- CSS
- Vanilla JavaScript
- MediaRecorder API

No frontend framework is required.

---

## 8. Frontend JavaScript

When the `/recognize` request succeeds:

```javascript
recognizedText.textContent = data.text;
commandText.textContent = data.command;
```

The UI should continue to show:

```text
Ready
Recording...
Processing...
```

and display an error if the request fails.

Do not add unnecessary UI components.

---

## 9. Full Processing Flow

```text
             Microphone
                  ↓
           MediaRecorder
                  ↓
              Browser
                  ↓
          POST /recognize
                  ↓
             Audio data
                  ↓
        ┌───────────────────┐
        │ Local Wav2Vec2    │
        │ Vietnamese ASR    │
        └─────────┬─────────┘
                  ↓
          Vietnamese text
                  ↓
        ┌───────────────────┐
        │ Command Classifier│
        └─────────┬─────────┘
                  ↓
       ┌──────────┼──────────┐
       ↓          ↓          ↓
   LIGHT_ON    FAN_ON     UNKNOWN
   LIGHT_OFF   FAN_OFF
```

---

## 10. Example Test Cases

```text
"bật đèn"
→ LIGHT_ON

"mở đèn lên"
→ LIGHT_ON

"tắt đèn"
→ LIGHT_OFF

"cho đèn tắt"
→ LIGHT_OFF

"bật quạt"
→ FAN_ON

"mở cái quạt"
→ FAN_ON

"cho quạt chạy"
→ FAN_ON

"tắt quạt"
→ FAN_OFF

"dừng quạt"
→ FAN_OFF

"chúc mừng sinh nhật"
→ UNKNOWN
```

The classifier should also handle additional words when the supported phrase
is present:

```text
"bật đèn phòng khách"
→ LIGHT_ON

"bật cái quạt trong phòng"
→ FAN_ON
```

---

## 11. Error Handling

### No audio

Return:

```json
{
    "success": false,
    "error": "No audio file provided"
}
```

### Invalid audio

Return an appropriate error message without crashing the server.

### Model loading failure

Fail clearly at application startup and print the model path being used.

### Unknown command

Do not treat it as an error. Return:

```text
UNKNOWN
```

---

## 12. Important Constraints

- Keep the existing Wav2Vec2 model.
- Use the model locally.
- Do not download models during runtime.
- Do not add another AI model.
- Do not implement GPIO yet.
- Do not implement Raspberry Pi communication yet.
- Do not implement authentication.
- Do not implement a database.
- Do not implement user accounts.
- Keep the project simple and easy to debug.

---

## 13. Future GPIO Integration

The current system stops at:

```text
Audio
 ↓
Vietnamese Text
 ↓
Command
```

A future stage will add:

```text
LIGHT_ON
    ↓
Raspberry Pi GPIO
    ↓
LED ON
```

and:

```text
FAN_ON
    ↓
Raspberry Pi GPIO
    ↓
Fan ON
```

Do not implement this stage now.

---

## 14. Future Commands

The architecture should make it easy to add:

```text
MOTOR_FORWARD
MOTOR_BACKWARD
MOTOR_STOP
SERVO_OPEN
SERVO_CLOSE
```

without changing the Wav2Vec2 part.

Only the command classification layer should need to be extended.
