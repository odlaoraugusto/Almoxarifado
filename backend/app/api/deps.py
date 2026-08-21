"""Dependências de autenticação/autorização compartilhadas pelos routers.

Sessão via JWT assinado pelo servidor. Diferente da farmácia, não existe
conceito de "unidade ativa" aqui — o almoxarifado tem um único estoque
central, então a sessão só carrega identidade + perfil.
"""

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decodificar_access_token
from app.database.session import get_db
from app.models.enums import PerfilEnum
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.usuario import UsuarioMe

_security = HTTPBearer(auto_error=True)
_usuario_repository = UsuarioRepository()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_security),
    db: Session = Depends(get_db),
) -> UsuarioMe:
    try:
        payload = decodificar_access_token(credentials.credentials)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão inválida ou expirada. Faça login novamente.",
        )

    usuario_id = payload.get("sub")
    if usuario_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão inválida.",
        )

    usuario = _usuario_repository.get_by_id(db, int(usuario_id))
    if usuario is None or not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário inexistente ou inativo.",
        )

    return UsuarioMe.model_validate(usuario)


def exigir_perfis(*perfis_permitidos: PerfilEnum):
    """Factory de dependência para restringir um endpoint a um subconjunto
    de perfis. Uso: `Depends(exigir_perfis(PerfilEnum.coordenador))`."""

    def verificador(usuario: UsuarioMe = Depends(get_current_user)) -> UsuarioMe:
        if usuario.perfil not in perfis_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Perfil sem permissão para esta operação.",
            )

        return usuario

    return verificador
