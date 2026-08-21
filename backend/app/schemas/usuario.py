from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import PerfilEnum


class UsuarioResumo(BaseModel):
    """Visão mínima de usuário — usada dentro de outras respostas (ex.
    quem registrou uma movimentação), sem expor login/hash."""

    id: int
    nome: str
    perfil: PerfilEnum

    model_config = ConfigDict(from_attributes=True)


class UsuarioMe(BaseModel):
    id: int
    nome: str
    login: str
    perfil: PerfilEnum
    deve_trocar_senha: bool = False

    model_config = ConfigDict(from_attributes=True)


class UsuarioCreate(BaseModel):
    """Gestão de usuários — exclusiva do Coordenador. `login` só existe
    aqui, nunca em `UsuarioUpdate`: é a chave que toda a trilha de
    auditoria referencia indiretamente (via `usuario_id`), então não faz
    sentido deixar mudar depois de criado."""

    nome: str
    login: str
    senha: str
    perfil: PerfilEnum


class UsuarioUpdate(BaseModel):
    nome: str | None = None
    perfil: PerfilEnum | None = None
    ativo: bool | None = None
    # Opcional — só reseta a senha quando vem preenchida (fluxo de "voltou
    # do esquecimento de senha"). Nunca devolvida em nenhuma resposta.
    senha: str | None = None


class UsuarioOut(BaseModel):
    id: int
    nome: str
    login: str
    perfil: PerfilEnum
    ativo: bool
    deve_trocar_senha: bool
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)
