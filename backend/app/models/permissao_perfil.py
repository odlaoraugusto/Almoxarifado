from sqlalchemy import Boolean, Column, Enum

from app.database.database import Base
from app.models.enums import PerfilEnum


class PermissaoPerfil(Base):
    """Matriz de permissões configurável, editável só pelo Admin (tela
    `/permissoes`). Só existe linha para `coordenador` e `atendente` — o
    perfil `admin` é superusuário implícito e nunca é consultado aqui
    (ver `app/api/deps.py::exigir_permissao`)."""

    __tablename__ = "permissoes_perfil"

    perfil = Column(
        Enum(PerfilEnum, name="perfil_enum", native_enum=False, length=20),
        primary_key=True,
    )

    ajustar_estoque = Column(Boolean, nullable=False, server_default="false")
    gerenciar_itens = Column(Boolean, nullable=False, server_default="false")
    gerenciar_setores = Column(Boolean, nullable=False, server_default="false")
    gestao_usuarios = Column(Boolean, nullable=False, server_default="false")
    relatorio_movimentacoes = Column(Boolean, nullable=False, server_default="false")
    descarte_vencimento = Column(Boolean, nullable=False, server_default="false")
