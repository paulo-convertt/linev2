import uvicorn
from fastapi import FastAPI
from whatsapp.webhook import app as webhook_app
from database.config import engine
from database.models import Base
import os

# Cria tabelas do banco
Base.metadata.create_all(bind=engine)

# Aplicação principal
app = FastAPI(title="Consórcio na Rede - Line Chatbot")

# Inclui rotas do WhatsApp
app.mount("/whatsapp", webhook_app)

@app.get("/")
async def root():
    return {
        "message": "Line Chatbot - Consórcio na Rede",
        "status": "online",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
