from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TipoMovimentacaoEnum
from app.schemas.lote import LoteDetalhadoOut
from app.schemas.usuario import UsuarioResumo


class AjusteCreate(BaseModel):
    """Ajuste de estoque — exclusivo do Coordenador. `quantidade_nova` é o
    saldo correto do lote depois de uma contagem física; o service
    calcula o delta contra o saldo atual, não o cliente (mesmo padrão da
    farmácia)."""

    lote_id: int
    quantidade_nova: int = Field(ge=0)
    motivo_ajuste: str


class DescarteCreate(BaseModel):
    """Baixa de lote vencido (2026-09-02, pedido do cliente) — sempre
    reduz o saldo do lote informado (nunca aceita um "novo saldo" pra
    cima como o Ajuste); motivo obrigatório pra manter a trilha de
    auditoria explicável. `lote_id` é sempre explícito, nunca resolvido
    por FEFO a partir de um item — baixa por vencimento precisa mirar
    exatamente o lote vencido, não o que "vence primeiro" entre todos os
    lotes do item (ver `app/services/consumo_fefo.py`, usado só pros
    fluxos de consumo normal de Pedido/Empréstimo)."""

    lote_id: int
    quantidade: int = Field(gt=0)
    motivo_descarte: str


class MovimentacaoOut(BaseModel):
    id: int
    tipo: TipoMovimentacaoEnum
    lote_id: int
    quantidade: int
    pedido_item_id: int | None
    emprestimo_id: int | None
    motivo_ajuste: str | None
    motivo_descarte: str | None
    usuario_id: int
    data_hora: datetime

    model_config = ConfigDict(from_attributes=True)


class MovimentacaoDetalhadaOut(MovimentacaoOut):
    lote: LoteDetalhadoOut
    usuario: UsuarioResumo

    model_config = ConfigDict(from_attributes=True)
