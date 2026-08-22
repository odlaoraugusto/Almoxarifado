/** Formatação compartilhada — evita duplicar Intl.* em cada página. */

export function formatarMoeda(valor: string | number | null | undefined): string {
  if (valor === null || valor === undefined || valor === '') return '—';
  const numero = typeof valor === 'string' ? Number(valor) : valor;
  if (Number.isNaN(numero)) return '—';
  return numero.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

export function formatarData(iso: string | null | undefined): string {
  if (!iso) return '—';
  const data = new Date(iso.length === 10 ? `${iso}T00:00:00` : iso);
  if (Number.isNaN(data.getTime())) return '—';
  return data.toLocaleDateString('pt-BR');
}

export function formatarDataHora(iso: string | null | undefined): string {
  if (!iso) return '—';
  const data = new Date(iso);
  if (Number.isNaN(data.getTime())) return '—';
  return data.toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' });
}

/** Dias corridos entre hoje e a data de validade (negativo = já venceu). */
export function diasAteVencer(dataValidade: string): number {
  const hoje = new Date();
  hoje.setHours(0, 0, 0, 0);
  const validade = new Date(`${dataValidade}T00:00:00`);
  return Math.round((validade.getTime() - hoje.getTime()) / (1000 * 60 * 60 * 24));
}

/** Nível de alerta de vencimento — mesma régua de 3 níveis usada na
 * farmácia (../estoque-farmacia-ref/frontend/src/lib/formato.ts):
 * vencido (vermelho), menos de 30 dias (amarelo), entre 30 e 60 dias
 * (roxo). Lotes sem validade (material que não vence) nunca entram
 * nessa régua — ver uso em EstoquePage. */
export type NivelValidade = 'vencido' | 'amarelo' | 'roxo' | 'ok';

export function nivelValidade(dias: number): NivelValidade {
  if (dias < 0) return 'vencido';
  if (dias < 30) return 'amarelo';
  if (dias <= 60) return 'roxo';
  return 'ok';
}

const PERFIL_LABEL: Record<string, string> = {
  coordenador: 'Coordenador',
  atendente: 'Atendente',
};
export function labelPerfil(perfil: string): string {
  return PERFIL_LABEL[perfil] ?? perfil;
}

const STATUS_PEDIDO_LABEL: Record<string, string> = {
  pendente: 'Pendente',
  parcial: 'Parcial',
  executado: 'Executado',
};
export function labelStatusPedido(status: string): string {
  return STATUS_PEDIDO_LABEL[status] ?? status;
}
export function pillStatusPedido(status: string): string {
  if (status === 'pendente') return 'pill pend';
  if (status === 'parcial') return 'pill roxo';
  if (status === 'executado') return 'pill ok';
  return 'pill muted';
}

const ORIGEM_LOTE_LABEL: Record<string, string> = { compra: 'Compra', doacao: 'Doação' };
export function labelOrigemLote(origem: string): string {
  return ORIGEM_LOTE_LABEL[origem] ?? origem;
}

const TIPO_MOV_LABEL: Record<string, string> = {
  entrada: 'Entrada',
  saida: 'Saída',
  ajuste: 'Ajuste',
};
export function labelTipoMovimentacao(tipo: string): string {
  return TIPO_MOV_LABEL[tipo] ?? tipo;
}
