from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.schemas.emprestimo import EmprestimoCreate, EmprestimoOut
from app.schemas.usuario import UsuarioMe
from app.services.emprestimo_service import EmprestimoService

router = APIRouter(prefix="/emprestimos", tags=["Empréstimos e Permutas"])

service = EmprestimoService()


@router.post("", response_model=EmprestimoOut, status_code=status.HTTP_201_CREATED)
def criar_emprestimo(
    dados: EmprestimoCreate,
    usuario: UsuarioMe = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Empréstimo/permuta com uma unidade EXTERNA (fora do catálogo
    interno de `setores`) — qualquer perfil autenticado registra, mesmo
    nível de permissão de quem já registra Entrada por compra/doação
    (`POST /itens/{item_id}/entrada`).

    `direcao=saida`: consome estoque nosso via FEFO. `direcao=entrada`:
    cria lote(s) novo(s) (devolução ou recebimento em permuta)."""
    return service.criar(db, usuario, dados)


@router.get("", response_model=list[EmprestimoOut])
def listar_emprestimos(
    usuario: UsuarioMe = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Histórico completo de empréstimos/permutas, mais recentes primeiro
    — equipe pequena, todo mundo enxerga tudo (mesmo critério de
    `GET /pedidos`)."""
    return service.listar(db)
