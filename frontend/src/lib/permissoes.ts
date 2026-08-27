import type { PermissaoPerfil, UsuarioMe } from '../types';

/** Espelha a matriz configurável de `/permissoes` (tela exclusiva do
 * Admin) — o frontend só reage a ela pra decidir o que mostrar/esconder.
 * Conferir pedido, registrar entrada e ver estoque/relatório de pedidos
 * são liberados a qualquer perfil autenticado; as 5 ações abaixo
 * dependem do que o Admin configurou para Coordenador/Atendente. O
 * Admin em si é superusuário implícito — não tem linha na matriz,
 * sempre vê tudo liberado, e é o único que enxerga a tela Permissões. */
export function permissoesDe(usuario: UsuarioMe | null, matriz: PermissaoPerfil[] | null) {
  const perfil = usuario?.perfil;
  const ehAdmin = perfil === 'admin';
  const linha = !ehAdmin && perfil ? (matriz?.find((p) => p.perfil === perfil) ?? null) : null;

  return {
    // Ajuste de estoque fora do fluxo normal (divergência de contagem).
    ajustarEstoque: ehAdmin || linha?.ajustar_estoque === true,

    // Cadastro/edição de itens do catálogo.
    gerenciarItens: ehAdmin || linha?.gerenciar_itens === true,

    // Cadastro de setores solicitantes.
    gerenciarSetores: ehAdmin || linha?.gerenciar_setores === true,

    // Gestão de usuários (não inclui promover alguém a Admin — isso é
    // exclusivo do próprio Admin, sempre, independente desta matriz).
    gestaoUsuarios: ehAdmin || linha?.gestao_usuarios === true,

    // Relatório de movimentações / trilha de auditoria completa.
    relatorioMovimentacoes: ehAdmin || linha?.relatorio_movimentacoes === true,

    // Tela /permissoes — exclusiva do Admin, nunca configurável.
    gerenciarPermissoes: ehAdmin,
  };
}

export type Permissoes = ReturnType<typeof permissoesDe>;
