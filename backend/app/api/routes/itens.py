from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import exigir_permissao, get_current_user
from app.database.session import get_db
from app.schemas.item import ItemCreate, ItemOut, ItemPublicoOut, ItemUpdate
from app.schemas.lote import EntradaCreate, LoteOut
from app.schemas.usuario import UsuarioMe
from app.services.item_service import ItemService

router = APIRouter(prefix="/itens", tags=["Itens"])

service = ItemService()

# Cadastro/edição do catálogo — controlado pela matriz de permissões
# (tela /permissoes, exclusiva do Admin — app/api/deps.py::exigir_permissao).
# Entrada de estoque é liberada para qualquer perfil autenticado (Atendente
# e Coordenador recebem compra/doação no dia a dia).
_PODE_CADASTRAR = exigir_permissao("gerenciar_itens")


@router.get("/publico", response_model=list[ItemPublicoOut])
def listar_itens_publico(db: Session = Depends(get_db)):
    """Sem autenticação — alimenta a busca de item do formulário público
    de pedido. Nunca expõe estoque_atual/estoque_minimo."""
    return service.listar_publico(db)


@router.get("", response_model=list[ItemOut], dependencies=[Depends(get_current_user)])
def listar_itens(incluir_inativos: bool = False, db: Session = Depends(get_db)):
    return service.listar(db, incluir_inativos)


@router.post("", response_model=ItemOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(_PODE_CADASTRAR)])
def criar_item(dados: ItemCreate, db: Session = Depends(get_db)):
    return service.criar(db, dados)


@router.put("/{item_id}", response_model=ItemOut, dependencies=[Depends(_PODE_CADASTRAR)])
def atualizar_item(item_id: int, dados: ItemUpdate, db: Session = Depends(get_db)):
    return service.atualizar(db, item_id, dados)


@router.post(
    "/{item_id}/entrada",
    response_model=LoteOut,
    status_code=status.HTTP_201_CREATED,
)
def registrar_entrada(
    item_id: int,
    dados: EntradaCreate,
    usuario: UsuarioMe = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.registrar_entrada(db, usuario, item_id, dados)
