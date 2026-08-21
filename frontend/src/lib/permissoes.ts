import type { UsuarioMe } from '../types';

/** Espelha a matriz de permissões do doc (seção 3.3) — o frontend só
 * reage a ela para decidir o que mostrar/esconder. Conferir pedido,
 * registrar entrada e ver estoque/relatório de saídas são liberados a
 * qualquer perfil autenticado; as 4 ações "administrativas" abaixo são
 * exclusivas do Coordenador. */
export function permissoesDe(usuario: UsuarioMe | null) {
  const perfil = usuario?.perfil;
  const ehCoordenador = perfil === 'coordenador';

  return {
    // Ajuste de estoque fora do fluxo normal (divergência de contagem).
    ajustarEstoque: ehCoordenador,

    // Cadastro/edição de itens do catálogo.
    gerenciarItens: ehCoordenador,

    // Cadastro de setores solicitantes.
    gerenciarSetores: ehCoordenador,

    // Gestão de usuários (os 5 logins do almoxarifado).
    gestaoUsuarios: ehCoordenador,

    // Relatório de movimentações / trilha de auditoria completa.
    relatorioMovimentacoes: ehCoordenador,
  };
}

export type Permissoes = ReturnType<typeof permissoesDe>;
