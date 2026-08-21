import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { baixarArquivo, mensagemErro } from '../lib/api';
import { permissoesDe } from '../lib/permissoes';
import { Alerta } from '../components/Alerta';
import type { StatusPedido } from '../types';

type AbaRelatorio = 'pedidos' | 'estoque' | 'vencimentos' | 'movimentacoes';

const TITULOS: Record<AbaRelatorio, string> = {
  pedidos: 'Pedidos',
  estoque: 'Estoque atual',
  vencimentos: 'Vencimentos próximos',
  movimentacoes: 'Movimentações (auditoria)',
};

// Caminhos conferidos direto contra as rotas do backend (app/api/routes/relatorios.py).
const CAMINHO_RELATORIO: Record<AbaRelatorio, string> = {
  pedidos: '/relatorios/pedidos',
  estoque: '/relatorios/estoque',
  vencimentos: '/relatorios/vencimentos',
  movimentacoes: '/relatorios/movimentacoes',
};

/** Exportação de relatórios em PDF/Excel — sem preview em tela, só
 * filtros + botões de download (o backend gera o arquivo pronto). */
export function RelatoriosPage() {
  const { token, usuario } = useAuth();
  const permissoes = permissoesDe(usuario);

  const abasDisponiveis: AbaRelatorio[] = permissoes.relatorioMovimentacoes
    ? ['pedidos', 'estoque', 'vencimentos', 'movimentacoes']
    : ['pedidos', 'estoque', 'vencimentos'];

  const [abaAtiva, setAbaAtiva] = useState<AbaRelatorio>('pedidos');
  const [status, setStatus] = useState<StatusPedido | ''>('');
  const [dataInicio, setDataInicio] = useState('');
  const [dataFim, setDataFim] = useState('');
  const [diasVencimento, setDiasVencimento] = useState('60');
  const [exportando, setExportando] = useState<'pdf' | 'excel' | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  const usaFiltroStatus = abaAtiva === 'pedidos';
  const usaFiltroData = abaAtiva === 'pedidos' || abaAtiva === 'movimentacoes';
  const usaFiltroDias = abaAtiva === 'vencimentos';

  async function exportar(formato: 'pdf' | 'excel') {
    setErro(null);
    setExportando(formato);
    try {
      await baixarArquivo(CAMINHO_RELATORIO[abaAtiva], {
        token,
        params: {
          formato,
          status: usaFiltroStatus ? status || undefined : undefined,
          data_inicio: usaFiltroData ? dataInicio || undefined : undefined,
          data_fim: usaFiltroData ? dataFim || undefined : undefined,
          dias: usaFiltroDias ? diasVencimento || undefined : undefined,
        },
      });
    } catch (err) {
      setErro(mensagemErro(err, 'Não foi possível gerar o arquivo.'));
    } finally {
      setExportando(null);
    }
  }

  return (
    <section>
      <div className="screen-head">
        <h1>Relatórios</h1>
        <span className="screen-tag">exportação em PDF / Excel</span>
      </div>
      <p className="screen-sub">Escolha o tipo de relatório, ajuste os filtros e exporte no formato desejado.</p>

      {erro && <Alerta tipo="erro">{erro}</Alerta>}

      <div className="tabs2" role="tablist">
        {abasDisponiveis.map((aba) => (
          <button key={aba} type="button" role="tab" className="tab2" aria-selected={abaAtiva === aba} onClick={() => setAbaAtiva(aba)}>
            {TITULOS[aba]}
          </button>
        ))}
      </div>

      <div className="panel">
        <div className="grid g3" style={{ marginBottom: 18 }}>
          {usaFiltroStatus && (
            <div className="field">
              <label htmlFor="rel-status">Status</label>
              <select id="rel-status" value={status} onChange={(e) => setStatus(e.target.value as StatusPedido | '')}>
                <option value="">Todos</option>
                <option value="pendente">Pendente</option>
                <option value="executado">Executado</option>
              </select>
            </div>
          )}
          {usaFiltroData && (
            <>
              <div className="field">
                <label htmlFor="rel-inicio">Período — de</label>
                <input id="rel-inicio" type="date" value={dataInicio} onChange={(e) => setDataInicio(e.target.value)} />
              </div>
              <div className="field">
                <label htmlFor="rel-fim">Período — até</label>
                <input id="rel-fim" type="date" value={dataFim} onChange={(e) => setDataFim(e.target.value)} />
              </div>
            </>
          )}
          {usaFiltroDias && (
            <div className="field">
              <label htmlFor="rel-dias">Vencendo em até (dias)</label>
              <input
                id="rel-dias"
                type="number"
                min={1}
                value={diasVencimento}
                onChange={(e) => setDiasVencimento(e.target.value)}
              />
            </div>
          )}
        </div>

        <p className="note" style={{ marginTop: 0 }}>
          O arquivo é gerado pelo servidor e baixado diretamente — não há pré-visualização nesta tela.
        </p>

        <div className="actions">
          <button type="button" className="btn ghost" disabled={exportando !== null} onClick={() => exportar('pdf')}>
            {exportando === 'pdf' ? 'Gerando PDF…' : 'Exportar PDF'}
          </button>
          <button type="button" className="btn ghost" disabled={exportando !== null} onClick={() => exportar('excel')}>
            {exportando === 'excel' ? 'Gerando Excel…' : 'Exportar Excel'}
          </button>
        </div>
      </div>
    </section>
  );
}
