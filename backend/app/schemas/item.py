from pydantic import BaseModel, ConfigDict

from app.models.enums import CategoriaItemEnum


class ItemCreate(BaseModel):
    codigo: str
    nome: str
    apresentacao: str
    categoria: CategoriaItemEnum
    estoque_minimo: int = 0
    fabricante: str | None = None


class ItemUpdate(BaseModel):
    codigo: str | None = None
    nome: str | None = None
    apresentacao: str | None = None
    categoria: CategoriaItemEnum | None = None
    estoque_minimo: int | None = None
    ativo: bool | None = None
    fabricante: str | None = None


class ItemPublicoOut(BaseModel):
    """Alimenta o formulário público de pedido (busca por código/nome) —
    sem estoque_atual/estoque_minimo, que nunca são expostos sem login."""

    id: int
    codigo: str
    nome: str
    apresentacao: str
    categoria: CategoriaItemEnum

    model_config = ConfigDict(from_attributes=True)


class ItemResumoOut(BaseModel):
    """Visão mínima do item — usada para embutir em `Lote`/`Movimentacao`/
    `PedidoItem` sem carregar o `estoque_atual` calculado (que exigiria
    uma soma de lotes extra por item embutido)."""

    id: int
    codigo: str
    nome: str
    apresentacao: str
    categoria: CategoriaItemEnum

    model_config = ConfigDict(from_attributes=True)


class ItemOut(BaseModel):
    id: int
    codigo: str
    nome: str
    apresentacao: str
    categoria: CategoriaItemEnum
    estoque_minimo: int
    ativo: bool
    fabricante: str | None = None

    # Calculado (não é coluna do model `Item`): soma de `Lote.quantidade_atual`
    # de todos os lotes deste item — ver `ItemRepository.listar_com_estoque`.
    estoque_atual: int

    model_config = ConfigDict(from_attributes=True)
