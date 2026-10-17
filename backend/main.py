
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.produtos import router as produtos_router
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

@app.get("/")
def inicio():
    return {
        "mensagem": "Backend da Burguesa Crochê funcionando!"
    }
