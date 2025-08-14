from flask import Flask, render_template, request, url_for, redirect, session, jsonify
from ultralytics import YOLO
import os
import uuid
import cv2
import requests
from datetime import datetime
import json
from functools import wraps

app = Flask(__name__, template_folder='templates')
app.secret_key = "super_secret_key_123"

# Kullanıcı bilgileri (Render environment variables ile alınıyor)
USERNAME = os.environ.get("ADMIN_USERNAME")
PASSWORD = os.environ.get("ADMIN_PASSWORD")

# Kayıt dosyası
DATA_FILE = "data.json"

# YOLO modeli
model = YOLO('runs/detect/train/weights/best.pt')

UPLOAD_FOLDER = 'static/uploads'
RESULT_FOLDER = 'static/results'
SNAPSHOT_FOLDER = 'static/snapshots'
ICON_PATH = 'static/icons/alarm.png'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)
os.makedirs(SNAPSHOT_FOLDER, exist_ok=True)

danger_state = False

# Telegram bilgileri (Render environment variables ile alınıyor)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Telegram gönderim fonksiyonu
def send_telegram_message(message):
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'HTML'}
    try:
        response = requests.post(url, data=payload)
        return response.ok
    except Exception as e:
        print("Telegram mesaj gönderilirken hata:", e)
        return False

# Login kontrol dekoratörü
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Admin login kontrolü
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get("username")
    password = request.form.get("password")
    if username == USERNAME and password == PASSWORD:
        session['username'] = username
        return redirect(url_for('admin_panel'))
    else:
        return render_template("index.html", error="Kullanıcı adı veya şifre hatalı!")

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

# Ana sayfa
@app.route('/')
def index():
    return render_template('index.html')

# Admin panel
@app.route('/admin')
@login_required
def admin_panel():
    if not os.path.exists(DATA_FILE):
        records = []
    else:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            records = json.load(f)
    return render_template("admin.html", records=records)

# Predict işlemi
@app.route('/predict', methods=['POST'])
def predict():
    global danger_state
    danger_state = False

    if 'file' not in request.files:
        return 'No file uploaded', 400
    file = request.files['file']
    if file.filename == '':
        return 'No file selected', 400

    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')

    filename = f"{uuid.uuid4().hex}_{file.filename}"
    upload_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(upload_path)

    cap = cv2.VideoCapture(upload_path)
    if not cap.isOpened():
        return 'Video açılamadı', 400

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    result_video_path = os.path.join(RESULT_FOLDER, f"processed_{filename}")
    out = cv2.VideoWriter(result_video_path, fourcc, fps, (width, height))

    snapshot_taken = False
    snapshot_path = None
    danger_times = []

    alarm_icon = cv2.imread(ICON_PATH, cv2.IMREAD_UNCHANGED) if os.path.exists(ICON_PATH) else None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_number = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
        current_time = frame_number / fps

        results = model.predict(frame, conf=0.5, verbose=False)
        annotated_frame = results[0].plot()

        boxes = results[0].boxes.xyxy.cpu().numpy().astype(int)
        detected_classes = results[0].boxes.cls.tolist()

        danger_in_frame = False

        for idx, cls in enumerate(detected_classes):
            if int(cls) == 0:
                danger_state = True
                danger_in_frame = True

                x1, y1, x2, y2 = boxes[idx]

                # Alarm ikon ekleme
                if alarm_icon is not None:
                    icon_resized = cv2.resize(alarm_icon, (50, 50))
                    h, w = icon_resized.shape[:2]
                    y_start = max(y1 - h, 0)
                    y_end = y_start + h
                    x_start = x1
                    x_end = x1 + w
                    if y_end <= annotated_frame.shape[0] and x_end <= annotated_frame.shape[1]:
                        annotated_frame[y_start:y_end, x_start:x_end] = icon_resized

                cv2.putText(
                    annotated_frame, "ALARM!",
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9, (0, 0, 255), 3
                )

                if not snapshot_taken:
                    snapshot_filename = f"snapshot_{uuid.uuid4().hex}.jpg"
                    snapshot_fullpath = os.path.join(SNAPSHOT_FOLDER, snapshot_filename)
                    cv2.imwrite(snapshot_fullpath, annotated_frame)
                    snapshot_path = f"snapshots/{snapshot_filename}"
                    snapshot_taken = True

        if danger_in_frame:
            danger_sec = round(current_time, 2)
            if len(danger_times) == 0 or abs(danger_times[-1] - danger_sec) > 0.5:
                danger_times.append(danger_sec)

        out.write(annotated_frame)

    cap.release()
    out.release()

    now = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    location_url = ""
    if latitude and longitude:
        location_url = f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}"

    if danger_state:
        message = (
            f"⚠️ <b>Tehlikeli nesne tespit edildi!</b>\n"
            f"Tarih-Saat: {now}\n"
            f"Video: {request.host_url}{url_for('static', filename=f'results/processed_{filename}')}\n"
            f"Anlar: {', '.join(str(t) + 's' for t in danger_times)}\n"
            f"📍 Konum: <a href='{location_url}'>Haritada Göster</a>"
        )
        send_telegram_message(message)

        # Admin panel kaydı
        record = {
            "tarih": now,
            "video": f"static/results/processed_{filename}",
            "tehlike_anlari": danger_times,
            "konum_link": location_url
        }
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = []
        data.append(record)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    # Snapshotlar
    danger_snapshots = []
    cap2 = cv2.VideoCapture(upload_path)
    for t in danger_times:
        cap2.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ret, frame = cap2.read()
        if ret:
            snapshot_filename = f"danger_{int(t*100)}.jpg"
            snapshot_fullpath = os.path.join(SNAPSHOT_FOLDER, snapshot_filename)
            cv2.imwrite(snapshot_fullpath, frame)
            snapshot_url = url_for('static', filename=f"snapshots/{snapshot_filename}")
            danger_snapshots.append((t, snapshot_url))
    cap2.release()

    return render_template(
        'result.html',
        image_path=f"results/processed_{filename}",
        snapshot_path=snapshot_path,
        danger=danger_state,
        danger_times=danger_times,
        danger_snapshots=danger_snapshots,
        detection_time=now
    )

# Durum kontrolü
@app.route('/status')
def status():
    return jsonify({"danger": danger_state})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
