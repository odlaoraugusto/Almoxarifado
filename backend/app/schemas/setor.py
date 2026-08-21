from pydantic import BaseModel, ConfigDict


class SetorCreate(BaseModel):
    nome: str


class SetorUpdate(BaseModel):
    nome: str | None = None
    ativo: bool | None = None


class SetorPublicoOut(BaseModel):
    """Só o necessário para o formulário público montar o <select> de
    setor — sem expor `ativo` (irrelevante para quem preenche)."""

    id: int
    nome: str

    model_config = ConfigDict(from_attributes=True)


class SetorOut(SetorPublicoOut):
    ativo: bool

    model_config = ConfigDict(from_attributes=True)
