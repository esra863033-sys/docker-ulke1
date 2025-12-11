# 1) Python 3.10 base imajını kullan
FROM python:3.10-slim

# Çalışma dizinini ayarla
WORKDIR /app

# requirements.txt dosyasını kopyala ve bağımlılıkları yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Tüm uygulama dosyalarını kopyala
COPY . .

# 2) Flask'ın varsayılan portu olan 5000'i dışarıya aç
EXPOSE 5000

# 3) Uygulamayı başlat
# Flask'ı tüm ağ arayüzlerinde (0.0.0.0) çalıştır
CMD ["python", "app.py"]
