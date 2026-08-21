from datetime import date

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.enums import StatusPedidoEnum
from app.schemas.pedido import PedidoCreate, PedidoDetalhadoOut, PedidoItemConferirCreate, PedidoItemOut
from app.schemas.usuario import UsuarioMe
from app.services.pedido_service import PedidoService

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])

service = PedidoService()


@router.post("", response_model=PedidoDetalhadoOut, status_code=status.HTTP_201_CREATED)
def criar_pedido(dados: PedidoCreate, db: Session = Depends(get_db)):
    """Sem autenticação — formulário público do setor. O `id` retornado
    serve de protocolo para o solicitante acompanhar o pedido."""
    return service.criar(db, dados)


@router.get("", response_model=list[PedidoDetalhadoOut])
def listar_pedidos(
    status: StatusPedidoEnum | None = None,
    setor_id: int | None = None,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    usuario: UsuarioMe = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Equipe pequena (5 pessoas): todo mundo enxerga a fila inteira."""
    return service.listar(db, status, setor_id, data_inicio, data_fim)


@router.get("/{pedido_id}", response_model=PedidoDetalhadoOut)
def obter_pedido(
    pedido_id: int,
    usuario: UsuarioMe = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.obter(db, pedido_id)


@router.patch("/{pedido_id}/itens/{pedido_item_id}/conferir", response_model=PedidoItemOut)
def conferir_item_pedido(
    pedido_id: int,
    pedido_item_id: int,
    dados: PedidoItemConferirCreate,
    usuario: UsuarioMe = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Conferência/liberação item a item — qualquer perfil autenticado
    (Atendente ou Coordenador) pode conferir, mesma regra de quem já
    registra entrada de estoque (matriz de permissões, seção 3.3 do
    doc)."""
    return service.conferir_item(db, usuario, pedido_id, pedido_item_id, dados)


@router.post("/{pedido_id}/executar-direto", response_model=PedidoDetalhadoOut)
def executar_pedido_direto(
    pedido_id: int,
    usuario: UsuarioMe = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Marca todos os itens ainda não conferidos como entregues igual ao
    solicitado, dando baixa real de estoque via FEFO — atalho para o dia
    corrido, sem abrir a tela de conferência item a item."""
    return service.executar_direto(db, usuario, pedido_id)
