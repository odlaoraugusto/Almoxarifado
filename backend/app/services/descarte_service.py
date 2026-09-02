from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.enums import TipoMovimentacaoEnum
from app.models.movimentacao import Movimentacao
from app.repositories.lote_repository import LoteRepository
from app.repositories.movimentacao_repository import MovimentacaoRepository
from app.schemas.movimentacao import DescarteCreate
from app.schemas.usuario import UsuarioMe


class DescarteService:
    """Baixa de lote vencido (2026-09-02, pedido do cliente) — trilha
    própria, separada do Ajuste (correção de contagem física): sempre
    reduz o saldo do lote indicado, nunca aceita um "novo saldo" pra
    cima, sempre com motivo obrigatório. Controlado pela matriz
    configurável (`descarte_vencimento`, router garante o perfil)."""

    def __init__(self):
        self.lote_repository = LoteRepository()
        self.movimentacao_repository = MovimentacaoRepository()

    def descartar(self, db: Session, usuario: UsuarioMe, dados: DescarteCreate) -> Movimentacao:
        lote = self.lote_repository.get_by_id_for_update(db, dados.lote_id)

        if lote is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Lote não encontrado."
            )

        if not dados.motivo_descarte or not dados.motivo_descarte.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Motivo da baixa é obrigatório.",
            )

        if dados.quantidade > lote.quantidade_atual:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Quantidade ({dados.quantidade}) maior que o saldo disponível "
                    f"no lote ({lote.quantidade_atual})."
                ),
            )

        lote.quantidade_atual -= dados.quantidade
        self.lote_repository.salvar(db, lote)

        movimentacao = Movimentacao(
            tipo=TipoMovimentacaoEnum.descarte,
            lote_id=lote.id,
            quantidade=dados.quantidade,
            motivo_descarte=dados.motivo_descarte.strip(),
            usuario_id=usuario.id,
        )

        return self.movimentacao_repository.create(db, movimentacao)
