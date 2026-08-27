from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import exigir_permissao, get_current_user
from app.database.session import get_db
from app.schemas.lote import LoteDetalhadoOut, LoteUpdate
from app.services.lote_service import LoteService

router = APIRouter(prefix="/lotes", tags=["Lotes"])

service = LoteService()

# Editar metadado do lote (valor unitário) fica junto do cadastro do
# item na matriz de permissões — mesma tela (Estoque), mesmo botão
# "Editar" conceitualmente.
_PODE_EDITAR = exigir_permissao("gerenciar_itens")


@router.get("", response_model=list[LoteDetalhadoOut], dependencies=[Depends(get_current_user)])
def listar_lotes(db: Session = Depends(get_db)):
    """Lista completa de lotes (qualquer perfil autenticado) — alimenta a
    tabela "Lotes" da tela de Estoque, incluindo os que já zeraram (não
    filtra saldo > 0, diferente de `listar_fefo`)."""
    return service.listar(db)


@router.put("/{lote_id}", response_model=LoteDetalhadoOut, dependencies=[Depends(_PODE_EDITAR)])
def atualizar_lote(lote_id: int, dados: LoteUpdate, db: Session = Depends(get_db)):
    """Correção pontual do valor unitário — nunca mexe em quantidade."""
    return service.atualizar(db, lote_id, dados)
