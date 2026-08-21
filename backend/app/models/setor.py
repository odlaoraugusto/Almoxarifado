from sqlalchemy import Boolean, Column, Integer, String

from app.database.database import Base


class Setor(Base):
    """Setor solicitante do hospital (docs/00_PROJETO_ALMOXARIFADO.md,
    seção 3.4) — cadastro simples, exclusivo do Coordenador, sem
    responsável fixo nem centro de custo associado."""

    __tablename__ = "setores"

    id = Column(Integer, primary_key=True)
    nome = Column(String(100), unique=True, nullable=False)
    ativo = Column(Boolean, nullable=False, default=True, server_default="true")
