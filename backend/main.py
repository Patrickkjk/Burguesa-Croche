from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env", override=True)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.produtos import router as produtos_router
from app.frete import router as frete_router   # NOVO
from app.database import criar_tabelas

criar_tabelas()


app = FastAPI(
    title="Burguesa Crochê API",
    description="API para gerenciamento de produtos da loja Burguesa Crochê",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(produtos_router)
app.include_router(frete_router)   # NOVO


@app.get("/")
def inicio():
    return {
        "mensagem": "Backend da Burguesa Crochê funcionando!"
    }