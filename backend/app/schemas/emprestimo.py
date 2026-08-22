from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import DirecaoEmprestimoEnum
from app.schemas.item import ItemResumoOut


class EmprestimoItemCreate(BaseModel):
    """`numero_lote`/`data_validade`/`valor_unitario` só fazem sentido
    quando `direcao=entrada` (viram atributos do lote novo criado) — são
    ignorados silenciosamente numa saída, mesma tolerância que o resto da
    API já tem para campos fora de contexto (não vale a pena travar com
    422 por um campo extra que o frontend pode mandar sem querer)."""

    item_id: int
    quantidade: int = Field(gt=0)
    numero_lote: str | None = None
    data_validade: date | None = None
    valor_unitario: Decimal | None = None


class EmprestimoCreate(BaseModel):
    direcao: DirecaoEmprestimoEnum
    unidade_origem: str
    numero_oficio: str | None = None
    itens: list[EmprestimoItemCreate] = Field(min_length=1)


class EmprestimoDetalheItemOut(BaseModel):
    """Um lote criado (direcao=entrada) ou uma linha de `Movimentacao` de
    saída gerada (direcao=saida) por este empréstimo, com o item já
    embutido — evita o frontend precisar cruzar `lote_id`/`movimentacao_id`
    manualmente contra outras rotas. `lote_id` e `movimentacao_id` são
    mutuamente exclusivos conforme a direção do registro pai."""

    item: ItemResumoOut
    quantidade: int
    lote_id: int | None = None
    movimentacao_id: int | None = None

    model_config = ConfigDict(from_attributes=True)


class EmprestimoOut(BaseModel):
    id: int
    direcao: DirecaoEmprestimoEnum
    unidade_origem: str
    numero_oficio: str | None
    usuario_id: int
    data_hora: datetime
    itens: list[EmprestimoDetalheItemOut]

    model_config = ConfigDict(from_attributes=True)
