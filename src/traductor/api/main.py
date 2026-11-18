"""API FastAPI (paso 4: se completa el endpoint /translate)."""
from fastapi import FastAPI

app = FastAPI(title="Traductor de texto en imagenes", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

# TODO (paso 2/4): POST /translate (recibe imagen + idioma destino, usa run_pipeline).
