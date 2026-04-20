# Hafif (slim) Python imajı
FROM python:3.10-slim

WORKDIR /app

# Önce sadece requirements'ı kopyala (Docker'ın cache avantajını kullanmak için)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Şimdi tüm kodları kopyala
COPY . .

# FastAPI'yi 8000 portundan dışarı açarak çalıştır
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]