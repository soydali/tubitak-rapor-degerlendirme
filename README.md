# TÜBİTAK Rapor Değerlendirme

Bu proje, TÜBİTAK 2204-A raporlarını yapay zeka kullanarak değerlendiren bir web uygulamasıdır.

## Özellikler

- PDF ve DOCX formatında rapor yükleme
- Gemini API kullanarak yapay zeka değerlendirmesi
- 100 üzerinden puanlama
- Geliştirme önerileri
- Modern ve kullanıcı dostu arayüz

## Kurulum

1. Python 3.8 veya daha yüksek bir sürümü yükleyin.

2. Projeyi klonlayın:
```bash
git clone [repo-url]
cd rapor-degerlendir
```

3. Sanal ortam oluşturun ve aktifleştirin:
```bash
python -m venv venv
# Windows için:
venv\Scripts\activate
# Linux/Mac için:
source venv/bin/activate
```

4. Gerekli paketleri yükleyin:
```bash
pip install -r requirements.txt
```

5. `.env` dosyası oluşturun ve Groq API anahtarınızı ekleyin:
```
API=your_api_key_here
```

## Çalıştırma

1. Flask uygulamasını başlatın:
```bash
python app.py
```

2. Tarayıcınızda `http://localhost:5000` adresine gidin.

## Kullanım

1. Ana sayfada "Dosya Seç" butonuna tıklayın
2. PDF veya DOCX formatında TÜBİTAK 2204-A raporunuzu seçin
3. "Değerlendir" butonuna tıklayın
4. Değerlendirme sonuçlarını görüntüleyin

## Gereksinimler

- Flask
- python-dotenv
- groq
- python-docx
- PyPDF2
- Werkzeug

## Lisans

MIT 
