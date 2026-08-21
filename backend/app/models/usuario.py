from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String
from sqlalchemy.sql import func

from app.database.database import Base
from app.models.enums import PerfilEnum


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True)

    nome = Column(String(150), nullable=False)
    login = Column(String(50), unique=True, nullable=False, index=True)
    senha_hash = Column(String(255), nullable=False)

    perfil = Column(
        Enum(PerfilEnum, name="perfil_enum", native_enum=False, length=20),
        nullable=False,
    )

    ativo = Column(Boolean, nullable=False, default=True, server_default="true")

    # Todo usuário novo (criado pela tela de Usuários ou pelo
    # scripts/seed_usuarios.py) nasce com este flag True e uma senha
    # temporária — o frontend deve forçar a troca de senha
    # (POST /auth/trocar-senha) antes de liberar o restante do painel.
    # Reset manual de senha pelo Coordenador (via PUT /usuarios/{id}) liga
    # o flag de novo.
    deve_trocar_senha = Column(Boolean, nullable=False, default=True, server_default="true")

    criado_em = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
