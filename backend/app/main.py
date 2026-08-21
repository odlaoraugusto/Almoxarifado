from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.routes.ajustes import router as ajustes_router
from app.api.routes.auth import router as auth_router
from app.api.routes.itens import router as itens_router
from app.api.routes.lotes import router as lotes_router
from app.api.routes.pedidos import router as pedidos_router
from app.api.routes.relatorios import router as relatorios_router
from app.api.routes.setores import router as setores_router
from app.api.routes.usuarios import router as usuarios_router
from app.core.config import settings
from app.database.database import engine

app = FastAPI(
    title="Almoxarifado — API",
    description=(
        f"{settings.HOSPITAL_ORGANIZACAO} — {settings.HOSPITAL_NOME}. "
        "Sistema de controle de almoxarifado: formulário público de "
        "pedido de material + painel de conferência/estoque da equipe."
    ),
)

_origens = (
    ["*"]
    if settings.CORS_ORIGINS.strip() == "*"
    else [origem.strip() for origem in settings.CORS_ORIGINS.split(",")]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origens,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(usuarios_router)
app.include_router(setores_router)
app.include_router(itens_router)
app.include_router(lotes_router)
app.include_router(pedidos_router)
app.include_router(ajustes_router)
app.include_router(relatorios_router)


@app.get("/")
def root():
    return {"message": "Almoxarifado API Online"}


@app.get("/health/database")
def health_database():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return {"database": "online"}
