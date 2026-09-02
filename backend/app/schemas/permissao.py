from pydantic import BaseModel, ConfigDict

from app.models.enums import PerfilEnum


class PermissaoPerfilOut(BaseModel):
    perfil: PerfilEnum
    ajustar_estoque: bool
    gerenciar_itens: bool
    gerenciar_setores: bool
    gestao_usuarios: bool
    relatorio_movimentacoes: bool
    descarte_vencimento: bool

    model_config = ConfigDict(from_attributes=True)


class PermissaoPerfilUpdate(BaseModel):
    ajustar_estoque: bool
    gerenciar_itens: bool
    gerenciar_setores: bool
    gestao_usuarios: bool
    relatorio_movimentacoes: bool
    descarte_vencimento: bool


class MatrizPermissoesUpdate(BaseModel):
    """Body do `PUT /permissoes` — exclusivo do Admin. Sempre as duas
    linhas juntas: a tela de Permissões sempre manda a matriz inteira,
    nunca uma atualização parcial de um perfil só."""

    coordenador: PermissaoPerfilUpdate
    atendente: PermissaoPerfilUpdate
