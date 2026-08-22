from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import OrigemEnum
from app.schemas.item import ItemResumoOut


class EntradaCreate(BaseModel):
    """Entrada de estoque — sempre cria um LOTE novo (nunca incrementa um
    lote já existente), mesmo padrão da farmácia: cada recebimento é um
    evento próprio, rastreável por si só."""

    numero_lote: str | None = None
    data_validade: date | None = None
    quantidade: int = Field(gt=0)
    valor_unitario: Decimal | None = None
    origem: OrigemEnum
    numero_nota_fiscal: str | None = None
    # Número de autorização usado em compras (opcional) — mesmo conceito
    # do projeto irmão da farmácia.
    numero_afm: str | None = None


class LoteOut(BaseModel):
    id: int
    item_id: int
    numero_lote: str | None
    data_validade: date | None
    quantidade_atual: int
    valor_unitario: Decimal | None
    origem: OrigemEnum
    numero_nota_fiscal: str | None
    numero_afm: str | None
    data_entrada: datetime
    usuario_entrada_id: int

    model_config = ConfigDict(from_attributes=True)


class LoteDetalhadoOut(LoteOut):
    item: ItemResumoOut

    model_config = ConfigDict(from_attributes=True)
