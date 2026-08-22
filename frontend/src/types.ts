// Tipos espelhando os schemas do backend (FastAPI), modelagem definitiva
// em docs/00_PROJETO_ALMOXARIFADO.md seção 4. Strings literais no lugar
// de `enum` porque o tsconfig do projeto usa `erasableSyntaxOnly`.
//
// O contrato de conferência de pedido (seção "Fluxos" do doc) descreve o
// comportamento mas não fixa o formato JSON exato dos endpoints — os
// nomes de rota/campo abaixo (`PATCH /pedidos/{id}/itens/{itemId}/conferir`
// etc.) são a melhor inferência a partir do fluxo descrito, documentada
// também no README. Ajustar aqui se o backend (agente almox-backend)
// expuser nomes diferentes.

export type Perfil = 'coordenador' | 'atendente';

export type StatusPedido = 'pendente' | 'parcial' | 'executado';

export type OrigemLote = 'compra' | 'doacao';

export type TipoMovimentacao = 'entrada' | 'saida' | 'ajuste';

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface UsuarioMe {
  id: number;
  nome: string;
  login: string;
  perfil: Perfil;
  deve_trocar_senha: boolean;
}

export interface UsuarioOut {
  id: number;
  nome: string;
  login: string;
  perfil: Perfil;
  ativo: boolean;
  deve_trocar_senha: boolean;
}

export interface Setor {
  id: number;
  nome: string;
  ativo: boolean;
}

/** Catálogo público — usado no formulário de pedido, sem exigir login. */
export interface ItemPublico {
  id: number;
  codigo: string;
  nome: string;
  apresentacao: string | null;
  categoria: string | null;
}

/** Catálogo com saldo agregado (Σ lotes) — usado nas telas autenticadas. */
export interface ItemOut extends ItemPublico {
  estoque_minimo: number;
  estoque_atual: number;
  ativo: boolean;
}

export interface ItemCriarPayload {
  codigo: string;
  nome: string;
  apresentacao?: string;
  categoria?: string;
  estoque_minimo: number;
}

export interface LoteOut {
  id: number;
  item_id: number;
  item?: ItemPublico;
  numero_lote: string | null;
  data_validade: string | null;
  quantidade_atual: number;
  valor_unitario: string | null;
  origem: OrigemLote;
  numero_nota_fiscal: string | null;
  numero_afm: string | null;
  data_entrada: string;
  usuario_entrada_id: number;
}

/** Corpo do `POST /itens/{item_id}/entrada` — item_id vai na URL, não no
 * payload. Usado pela tela "Entrada por Compra" (uma chamada por
 * item/linha adicionada, repetindo o cabeçalho nota fiscal/AFM em cada
 * uma). `numero_afm` é opcional no schema do backend — a tela de Entrada
 * por Compra que o torna obrigatório na UI quando fizer sentido. */
export interface EntradaCriarPayload {
  numero_lote?: string;
  data_validade?: string;
  quantidade: number;
  valor_unitario?: string;
  origem: OrigemLote;
  numero_nota_fiscal?: string;
  numero_afm?: string;
}

/** Direção de um registro de empréstimo/permuta com unidade externa
 * (fora do nosso catálogo de setores). "saida" consome estoque nosso;
 * "entrada" (devolução ou permuta) cria lote(s) novo(s), igual à Entrada
 * por Compra. */
export type DirecaoEmprestimo = 'entrada' | 'saida';

export interface EmprestimoItemPayload {
  item_id: number;
  quantidade: number;
  numero_lote?: string;
  data_validade?: string;
  valor_unitario?: string;
}

/** Corpo do `POST /emprestimos` — diferente da Entrada por Compra, aceita
 * a lista inteira de itens numa única chamada. Rota ainda não existe no
 * backend no momento em que este contrato foi escrito (construída em
 * paralelo pelo agente almox-backend-2) — nomes de campo seguem o
 * contrato combinado; ajustar aqui se o backend expuser algo diferente. */
export interface EmprestimoCriarPayload {
  direcao: DirecaoEmprestimo;
  unidade_origem: string;
  numero_oficio?: string;
  itens: EmprestimoItemPayload[];
}

/** Um lote criado (direcao=entrada) ou uma linha de saída gerada
 * (direcao=saida) por este empréstimo — `lote_id`/`movimentacao_id` são
 * mutuamente exclusivos conforme a direção do registro pai. Se o FEFO
 * precisar puxar de mais de um lote pra cobrir a quantidade de um item
 * numa saída, aquele item vira mais de uma linha aqui (sem
 * correspondência 1:1 com o array de itens enviado no POST). */
export interface EmprestimoItemOut {
  item: ItemPublico;
  quantidade: number;
  lote_id: number | null;
  movimentacao_id: number | null;
}

export interface EmprestimoOut {
  id: number;
  direcao: DirecaoEmprestimo;
  unidade_origem: string;
  numero_oficio: string | null;
  usuario_id: number;
  data_hora: string;
  itens: EmprestimoItemOut[];
}

export interface PedidoItemPayload {
  item_id: number;
  quantidade_solicitada: number;
}

/** Corpo do POST público (sem auth) — o "pedido de material" do setor. */
export interface PedidoCriarPayload {
  setor_id: number;
  responsavel_solicitante: string;
  observacao?: string;
  itens: PedidoItemPayload[];
}

export interface PedidoItemOut {
  id: number;
  pedido_id: number;
  item_id_solicitado: number;
  item_solicitado?: ItemPublico;
  quantidade_solicitada: number;
  item_id_entregue: number | null;
  item_entregue?: ItemPublico | null;
  quantidade_entregue: number | null;
  motivo_substituicao: string | null;
}

export interface PedidoOut {
  id: number;
  setor_id: number;
  setor?: Setor;
  responsavel_solicitante: string;
  observacao: string | null;
  data_hora: string;
  status: StatusPedido;
  data_execucao: string | null;
  usuario_execucao_id: number | null;
  usuario_execucao?: { id: number; nome: string; perfil: Perfil } | null;
  itens: PedidoItemOut[];
}

/** Corpo do PATCH de conferência de UM item do pedido — o item entregue
 * é sempre o solicitado (sem troca de item nesta tela). */
export interface ConferirItemPayload {
  quantidade_entregue: number;
}

/** O backend calcula o delta a partir de `quantidade_nova` contra o
 * saldo atual do lote — nunca aceita um delta pronto do cliente (mesmo
 * padrão da farmácia). */
export interface AjusteCriarPayload {
  lote_id: number;
  quantidade_nova: number;
  motivo_ajuste: string;
}

export interface MovimentacaoOut {
  id: number;
  tipo: TipoMovimentacao;
  lote_id: number;
  lote?: LoteOut;
  quantidade: number;
  pedido_item_id: number | null;
  motivo_ajuste: string | null;
  usuario_id: number;
  usuario_nome?: string;
  data_hora: string;
}
