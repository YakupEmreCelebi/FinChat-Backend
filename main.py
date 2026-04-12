from fastapi import FastAPI

# Uygulamayı başlatıyoruz
app = FastAPI()

@app.get("/")
def read_root():
    return {
        "status": "FinChat Backend Çalışıyor!",
        "message": "Merhaba Bilkent, Python dünyasına hoş geldin."
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}