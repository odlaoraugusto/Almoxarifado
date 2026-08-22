from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.enums import TipoMovimentacaoEnum
from app.models.movimentacao import Movimentacao
from app.repositories.lote_repository import LoteRepository
from app.repositories.movimentacao_repository import MovimentacaoRepository


def consumir_fefo(
    db: Session,
    lote_repository: LoteRepository,
    movimentacao_repository: MovimentacaoRepository,
    usuario_id: int,
    item_id: int,
    quantidade_necessaria: int,
    *,
    pedido_item_id: int | None = None,
    emprestimo_id: int | None = None,
) -> None:
    """Consome `quantidade_necessaria` unidades do item, priorizando o
    lote que vence primeiro (FEFO — First Expire, First Out, mesma lógica
    da farmácia), podendo atravessar mais de um lote. Cada lote tocado é
    travado com `SELECT ... FOR UPDATE` antes de decrementar, para não
    colidir com outra conferência/ajuste/empréstimo simultâneo no mesmo
    lote.

    Compartilhado entre `PedidoService` (baixa por conferência de pedido)
    e `EmprestimoService` (baixa por empréstimo/permuta enviado) — a
    única diferença entre os dois usos é qual FK de origem é gravada em
    cada `Movimentacao` de saída (`pedido_item_id` xor `emprestimo_id`,
    ambos opcionais e mutuamente exclusivos na prática, sem constraint
    para isso)."""
    lotes_disponiveis = lote_repository.listar_fefo(db, item_id)
    total_disponivel = sum(lote.quantidade_atual for lote in lotes_disponiveis)

    if total_disponivel < quantidade_necessaria:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Estoque insuficiente para o item id={item_id}: disponível "
                f"{total_disponivel}, necessário {quantidade_necessaria}."
            ),
        )

    restante = quantidade_necessaria
    for lote_candidato in lotes_disponiveis:
        if restante <= 0:
            break

        # Trava a linha antes de decrementar — a listagem acima já não
        # tem lock, então relê o saldo travado antes de usar.
        lote = lote_repository.get_by_id_for_update(db, lote_candidato.id)
        if lote is None or lote.quantidade_atual <= 0:
            continue

        consumido = min(restante, lote.quantidade_atual)
        lote.quantidade_atual -= consumido
        lote_repository.salvar(db, lote)

        movimentacao = Movimentacao(
            tipo=TipoMovimentacaoEnum.saida,
            lote_id=lote.id,
            quantidade=consumido,
            pedido_item_id=pedido_item_id,
            emprestimo_id=emprestimo_id,
            usuario_id=usuario_id,
        )
        movimentacao_repository.create(db, movimentacao)

        restante -= consumido

    if restante > 0:
        # Condição de corrida rara: outro atendente/operação consumiu
        # saldo entre a listagem e o lock. Falha limpa em vez de deixar a
        # operação marcada como concluída sem baixa completa.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Estoque do item id={item_id} mudou durante a conferência. "
                "Tente novamente."
            ),
        )
