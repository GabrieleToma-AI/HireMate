from fastapi import FastAPI
import uvicorn
from routers import sessions # o 'session', a seconda di come l'hai chiamato

# Inizializziamo l'app FastAPI con i metadati per la Swagger UI
app = FastAPI(
    title="HireMate GenAI API",
    description="Backend per il simulatore di colloqui HR. Sviluppato dal team GenAI.",
    version="0.1.0"
)

app.include_router(sessions.router, prefix="/api/session", tags=["Session"])
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
        "llm": "OpenAI/Gemini (da collegare)",
        "status": "healthy"
    }

# Questo blocco permette di avviare il server lanciando direttamente 'python main.py'
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)