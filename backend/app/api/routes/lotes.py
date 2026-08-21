from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.schemas.lote import LoteDetalhadoOut
from app.services.lote_service import LoteService

router = APIRouter(prefix="/lotes", tags=["Lotes"])

service = LoteService()


@router.get("", response_model=list[LoteDetalhadoOut], dependencies=[Depends(get_current_user)])
def listar_lotes(db: Session = Depends(get_db)):
    """Lista completa de lotes (qualquer perfil autenticado) — alimenta a
    tabela "Lotes" da tela de Estoque, incluindo os que já zeraram (não
    filtra saldo > 0, diferente de `listar_fefo`)."""
    return service.listar(db)
