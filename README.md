# Vietnamese Voice IoT

Ứng dụng web nhận dạng tiếng Việt bằng model Wav2Vec2 local và chuyển câu nói thành lệnh điều khiển thiết bị IoT.

Luồng xử lý:

```text
Microphone
    -> Browser MediaRecorder
    -> Flask HTTPS server
    -> Wav2Vec2 Vietnamese ASR
    -> Vietnamese text
    -> Command classifier
    -> ALL_ON / ALL_OFF / LIGHT_ON / LIGHT_OFF / FAN_ON / FAN_OFF / UNKNOWN
```

Dự án hiện hỗ trợ hai thiết bị:

- Đèn: `LIGHT_ON`, `LIGHT_OFF`
- Quạt: `FAN_ON`, `FAN_OFF`
- Tất cả thiết bị: `ALL_ON`, `ALL_OFF`

Ứng dụng có thể chạy trên Raspberry Pi với GPIO thông qua `lgpio`. Khi chạy trên máy không có GPIO, hệ thống tự chuyển sang simulation mode để vẫn có thể kiểm thử giao diện và nhận dạng giọng nói. Chưa triển khai tài khoản người dùng, cơ sở dữ liệu hay chức năng điều khiển khác.

## 1. Chuẩn bị Raspberry Pi

Cập nhật hệ thống và cài các gói cần cho Python, audio, HTTPS và GPIO:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip python3-dev \
    build-essential libsndfile1 openssl
```

Kiểm tra địa chỉ IP trong mạng LAN:

```bash
hostname -I
```

Ví dụ Raspberry Pi có IP `192.168.1.50`. Cần dùng địa chỉ này ở các bước tạo certificate và truy cập web.

## 2. Đưa mã nguồn lên Raspberry Pi

Clone repository hoặc chép toàn bộ project vào Raspberry Pi, sau đó đi tới thư mục project:

```bash
cd ~/voice_iot
```

Thư mục gốc cần có tối thiểu:

```text
app.py
command_classifier.py
hardware_controller.py
download_model.py
requirements.txt
templates/index.html
```

## 3. Tạo virtual environment

Tạo môi trường Python riêng cho project:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
```

Mỗi lần mở terminal mới, kích hoạt lại môi trường:

```bash
cd ~/voice_iot
source .venv/bin/activate
```

## 4. Cài môi trường Python

Cài các dependency của project:

```bash
pip install -r requirements.txt
```

Kiểm tra nhanh các module chính:

```bash
python -c "import flask, torch, transformers, librosa, av, lgpio; print('Environment OK')"
```

Nếu chỉ muốn chạy thử trên máy không có GPIO, bật simulation mode:

```bash
export VOICE_CONTROL_SIMULATE=1
```

Trên Raspberry Pi thật, không cần đặt biến này nếu muốn sử dụng GPIO.

## 5. Tải model Vietnamese Wav2Vec2

Model được tải một lần từ Hugging Face và lưu vào thư mục local. Bước này cần Internet:

```bash
source .venv/bin/activate
python download_model.py
```

Sau khi hoàn tất, cần có:

```text
models/wav2vec2-vietnamese-160h/
```

Ứng dụng không tải model khi khởi động. Khi chạy `app.py`, model luôn được đọc từ thư mục local với `local_files_only=True`.

## 6. Tạo HTTPS certificate theo IP Raspberry Pi

HTTPS cần thiết vì trình duyệt thường chỉ cho phép microphone trên `localhost` hoặc HTTPS. Tạo certificate tự ký trong thư mục `certs`:

```bash
mkdir -p certs
IP=$(hostname -I | awk '{print $1}')

openssl req -x509 -newkey rsa:2048 -nodes \
    -keyout certs/server.key \
    -out certs/server.crt \
    -days 365 \
    -subj "/CN=$IP" \
    -addext "subjectAltName=IP:$IP"
```

Lưu ý từ openssl trở đi là 1 dòng lệnh duy nhất (nếu chạy lệnh mà console yêu cầu nhập thêm thông tin thì có nghĩa là nó đã bị ngắt dòng hãy xóa "\\  \" để cho các parameters được nằm cùng 1 dòng )

Kiểm tra file:

```bash
ls -l certs/server.crt certs/server.key
```

Ứng dụng yêu cầu đúng hai file:

```text
certs/server.crt
certs/server.key
```

Certificate tự ký sẽ khiến trình duyệt hiện cảnh báo bảo mật. Đây là điều bình thường trong mạng nội bộ; chọn phần tiếp tục truy cập website sau khi xác nhận IP đúng.

## 7. Chạy server

```bash
source .venv/bin/activate
python app.py
```

Server lắng nghe trên mọi interface ở port `5000`:

```text
https://0.0.0.0:5000
```

Không dùng địa chỉ `0.0.0.0` để mở trên trình duyệt. Hãy dùng IP thật của Raspberry Pi, ví dụ:

```text
https://192.168.1.50:5000
```

## 8. Truy cập từ thiết bị khác

Điện thoại hoặc laptop cần kết nối cùng mạng LAN với Raspberry Pi. Mở trình duyệt và truy cập:

```text
https://<RASPBERRY_PI_IP>:5000
```

Ví dụ:

```text
https://192.168.1.50:5000
```

Sau khi chấp nhận cảnh báo certificate:

1. Cho phép quyền microphone.
2. Nhấn **Record**.
3. Nói câu lệnh tiếng Việt.
4. Nhấn **Stop**.
5. Xem transcript, action và trạng thái Đèn/Quạt.

Nếu Raspberry Pi bật UFW, cho phép port `5000`:

```bash
sudo ufw allow 5000/tcp
sudo ufw status
```

## 9. Kiểm tra nhanh

Kiểm tra trạng thái server:

```bash
curl -k https://127.0.0.1:5000/health
```

Kiểm tra classifier không cần microphone:

```bash
python command_classifier.py
```

Một số câu lệnh mẫu:

```text
bật đèn             -> LIGHT_ON
tắt đèn             -> LIGHT_OFF
bật quạt            -> FAN_ON
dừng quạt           -> FAN_OFF
chúc mừng sinh nhật -> UNKNOWN
```

Classifier có hỗ trợ câu không dấu và một số lỗi nhận dạng thường gặp, ví dụ `bat den` hoặc `bac den`.

## 10. Dừng server

Nhấn `Ctrl+C` trong terminal đang chạy server.

Nếu đã bật virtual environment, thoát bằng:

```bash
deactivate
```

## Lưu ý

- Không commit `.venv/`, model local, file ghi âm hoặc private key lên Git.
- Không chia sẻ `certs/server.key`.
- Certificate ở trên chỉ phù hợp cho mạng nội bộ và mục đích thử nghiệm.
- Để chạy GPIO thật, Raspberry Pi cần đấu nối đúng chân theo cấu hình trong `hardware_controller.py`.
