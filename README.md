# AlertSight
🚨 AlertSight – Tehlikeli Nesne Tespit ve Konum Bildirim Sistemi

AlertSight, yapay zeka destekli nesne tespiti ve konum takibi yapabilen bir web uygulamasıdır.
Proje, YOLO nesne tespit modeli kullanılarak geliştirilmiş ve kendi oluşturduğum veri seti ile fine-tuning yapılarak doğruluk oranı artırılmıştır.

✨ Özellikler

📷 Gerçek zamanlı tehlikeli nesne tespiti (YOLO ile)

📍 Konum tespiti – Tarayıcı Geolocation API ile konum bilgisi alma

🗺 Harita üzerinde görselleştirme – Leaflet.js kütüphanesi ile

🌐 Web tabanlı arayüz – HTML, CSS ve JavaScript ile kullanıcı dostu tasarım

⚙️ Flask tabanlı backend – HTTP isteklerinin yönetilmesi ve veri işleme

🛠 Model eğitimi – Kendi veri setimle fine-tuning işlemi

🖥 Kullanılan Teknolojiler

Teknoloji / Araç	Açıklama
YOLO	Nesne tespiti için derin öğrenme modeli
Flask	Python tabanlı web backend framework
HTML / CSS / JS	Kullanıcı arayüzü geliştirme
Geolocation API	Konum verisi elde etme
Leaflet.js	Harita üzerinde konum gösterimi
OpenCV	Görüntü işleme ve video akışı yönetimi


📂 Proje Yapısı
AlertSight/
│
├── static/               # CSS, JS ve görseller
├── templates/            # HTML dosyaları
├── yolov_model/          # Eğitilmiş YOLO model ağırlıkları
├── app.py                # Flask backend ana dosyası
├── requirements.txt      # Gerekli Python paketleri
└── README.md             # Proje açıklaması

🚀 Çalıştırma Adımları

Gerekli bağımlılıkları yükleyin:

pip install -r requirements.txt


Flask sunucusunu başlatın:

python app.py


Tarayıcıdan uygulamayı açın:

http://127.0.0.1:5000

🎯 Proje Amacı

Bu proje, tehlikeli nesnelerin gerçek zamanlı olarak tespit edilmesini ve konum bilgilerinin harita üzerinde gösterilmesini amaçlamaktadır. Böylece olay anında hızlı ve etkili müdahale sağlanabilir.

🙌 Teşekkür

Bu proje, Up School AI First Developer Programı kapsamında, değerli mentorlarım ve eğitmenlerimin desteğiyle geliştirilmiştir.
