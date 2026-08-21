from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import exigir_perfis
from app.database.session import get_db
from app.models.enums import PerfilEnum
from app.schemas.movimentacao import AjusteCreate, MovimentacaoDetalhadaOut
from app.schemas.usuario import UsuarioMe
from app.services.ajuste_service import AjusteService

router = APIRouter(prefix="/ajustes", tags=["Ajustes"])

service = AjusteService()

# Ajuste de estoque — exclusivo do Coordenador (matriz de permissões,
# docs/00_PROJETO_ALMOXARIFADO.md seção 3.3): corrige saldo fora dos
# fluxos normais (ex. divergência de contagem física).
_PODE_AJUSTAR = exigir_perfis(PerfilEnum.coordenador)


@router.post("", response_model=MovimentacaoDetalhadaOut)
def ajustar_estoque(
    dados: AjusteCreate,
    usuario: UsuarioMe = Depends(_PODE_AJUSTAR),
    db: Session = Depends(get_db),
):
    return service.ajustar(db, usuario, dados)
