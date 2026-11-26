import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from routers import cv, sessions, users  # sessions/users: Stream 3 (users) e Collega 1

# Inizializziamo l'app FastAPI con i metadati per la Swagger UI
app = FastAPI(
    title="HireMate GenAI API",
    description="Backend per il simulatore di colloqui HR. Sviluppato dal team GenAI.",
    version="0.1.0"
)

# Il frontend gira su un'altra origine (es. Vite su :5173): senza CORS il browser blocca le chiamate.
origini = os.getenv(
    "CORS_ALLOW_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origini.split(",") if o.strip()],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router, prefix="/api/session", tags=["Session"])
app.include_router(cv.router, prefix="/api/cv", tags=["CV"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])  # Collega 1

# Endpoint base di test (Root)
@app.get("/")
def read_root():
    """
    Endpoint di benvenuto. Serve solo a verificare che il server sia attivo.
    """
    return {
        "status": "success",
        "message": "HireMate AI Engine is running! 🚀",
        "docs_url": "Vai su /docs per la Swagger UI"
    }

# Esempio di endpoint specifico per HireMate
@app.get("/api/health")
def health_check():
    """
    Endpoint di health check per verificare lo stato del backend.
    """
    return {
        "engine": "GenAI",
        "database": "Supabase (da collegare)",
        "llm": "FreeLLMAPI / Gemini 3.5 Flash-Lite / DeepSeek",
        "status": "healthy"
    }

# Questo blocco permette di avviare il server lanciando direttamente 'python main.py'
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
