import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { api, baixarArquivo, mensagemErro } from '../lib/api';
import { permissoesDe } from '../lib/permissoes';
import { Alerta } from '../components/Alerta';
import {
  formatarData,
  formatarDataHora,
  labelCategoriaItem,
  labelNivelVencimentoRelatorio,
  labelStatusPedido,
  labelTipoMovimentacao,
  pillStatusPedido,
} from '../lib/formato';
import type {
  RelatorioEstoqueOut,
  RelatorioMovimentacoesOut,
  RelatorioPedidosOut,
  RelatorioVencimentosOut,
  StatusPedido,
} from '../types';

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

/** Exportação de relatórios em PDF/Excel, com prévia em tela — a prévia
 * usa o mesmo endpoint da exportação, só que sem o parâmetro `formato`
 * (o backend devolve o JSON que alimentaria o PDF/Excel em vez do
 * arquivo pronto, ver `app/api/routes/relatorios.py`), então as colunas
 * na tela são exatamente as mesmas do arquivo exportado. */
export function RelatoriosPage() {
  const { token, usuario, matrizPermissoes } = useAuth();
  const permissoes = permissoesDe(usuario, matrizPermissoes);

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

  function trocarAba(aba: AbaRelatorio) {
    setAbaAtiva(aba);
    setPrevia(null);
    setErroPrevia(null);
  }

  const parametrosAtuais = {
    status: usaFiltroStatus ? status || undefined : undefined,
    data_inicio: usaFiltroData ? dataInicio || undefined : undefined,
    data_fim: usaFiltroData ? dataFim || undefined : undefined,
    dias: usaFiltroDias ? diasVencimento || undefined : undefined,
  };

  async function exportar(formato: 'pdf' | 'excel') {
    setErro(null);
    setExportando(formato);
    try {
      await baixarArquivo(CAMINHO_RELATORIO[abaAtiva], { token, params: { formato, ...parametrosAtuais } });
    } catch (err) {
      setErro(mensagemErro(err, 'Não foi possível gerar o arquivo.'));
    } finally {
      setExportando(null);
    }
  }

  // ---- prévia em tela ----
  type Previa = RelatorioPedidosOut | RelatorioEstoqueOut | RelatorioVencimentosOut | RelatorioMovimentacoesOut;
  const [previa, setPrevia] = useState<Previa | null>(null);
  const [carregandoPrevia, setCarregandoPrevia] = useState(false);
  const [erroPrevia, setErroPrevia] = useState<string | null>(null);

  async function carregarPrevia() {
    setErroPrevia(null);
    setCarregandoPrevia(true);
    try {
      const dados = await api.get<Previa>(CAMINHO_RELATORIO[abaAtiva], { token, params: parametrosAtuais });
      setPrevia(dados);
    } catch (err) {
      setErroPrevia(mensagemErro(err, 'Não foi possível carregar a prévia.'));
      setPrevia(null);
    } finally {
      setCarregandoPrevia(false);
    }
  }

  return (
    <section>
      <div className="screen-head">
        <h1>Relatórios</h1>
        <span className="screen-tag">prévia em tela + exportação em PDF / Excel</span>
      </div>
      <p className="screen-sub">Escolha o tipo de relatório, ajuste os filtros, veja a prévia e exporte no formato desejado.</p>

      {erro && <Alerta tipo="erro">{erro}</Alerta>}

      <div className="tabs2" role="tablist">
        {abasDisponiveis.map((aba) => (
          <button key={aba} type="button" role="tab" className="tab2" aria-selected={abaAtiva === aba} onClick={() => trocarAba(aba)}>
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
                <option value="parcial">Parcial</option>
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

        <div className="actions" style={{ marginTop: 0 }}>
          <button type="button" className="btn" disabled={carregandoPrevia} onClick={carregarPrevia}>
            {carregandoPrevia ? 'Carregando…' : previa ? 'Atualizar prévia' : 'Ver prévia'}
          </button>
          <button type="button" className="btn ghost" disabled={exportando !== null} onClick={() => exportar('excel')}>
            {exportando === 'excel' ? 'Gerando Excel…' : 'Exportar Excel'}
          </button>
          <button type="button" className="btn ghost" disabled={exportando !== null} onClick={() => exportar('pdf')}>
            {exportando === 'pdf' ? 'Gerando PDF…' : 'Exportar PDF'}
          </button>
        </div>
      </div>

      {erroPrevia && <Alerta tipo="erro">{erroPrevia}</Alerta>}

      {previa && (
        <div className="panel">
          <h2>
            Prévia — {TITULOS[abaAtiva]} <span className="screen-tag">{previa.metadados.gerado_em && formatarDataHora(previa.metadados.gerado_em)}</span>
          </h2>
          <PreviaTabela aba={abaAtiva} dados={previa} />
        </div>
      )}
    </section>
  );
}

function PreviaTabela({
  aba,
  dados,
}: {
  aba: AbaRelatorio;
  dados: RelatorioPedidosOut | RelatorioEstoqueOut | RelatorioVencimentosOut | RelatorioMovimentacoesOut;
}) {
  if (aba === 'pedidos') {
    const relatorio = dados as RelatorioPedidosOut;
    const linhas = relatorio.itens.flatMap((pedido) =>
      pedido.itens.map((item) => ({ pedido, item })),
    );
    return (
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Pedido</th>
              <th>Setor</th>
              <th>Responsável</th>
              <th>Status</th>
              <th>Item</th>
              <th className="num">Qtd. Solicitada</th>
              <th className="num">Qtd. Dispensada</th>
              <th>Data/Hora</th>
              <th>Executado Por</th>
            </tr>
          </thead>
          <tbody>
            {linhas.length === 0 && (
              <tr>
                <td colSpan={9} className="vazio-tabela">
                  Nenhum pedido encontrado com esse filtro.
                </td>
              </tr>
            )}
            {linhas.map(({ pedido, item }) => (
              <tr key={item.id}>
                <td className="mono">#{pedido.id}</td>
                <td>{pedido.setor?.nome ?? `#${pedido.setor_id}`}</td>
                <td>{pedido.responsavel_solicitante}</td>
                <td>
                  <span className={pillStatusPedido(pedido.status)}>{labelStatusPedido(pedido.status)}</span>
                </td>
                <td>{item.item_solicitado?.nome ?? `item #${item.item_id_solicitado}`}</td>
                <td className="num">{item.quantidade_solicitada}</td>
                <td className="num">{item.quantidade_entregue ?? '—'}</td>
                <td className="mono">{formatarDataHora(pedido.data_hora)}</td>
                <td>{pedido.usuario_execucao?.nome ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  if (aba === 'estoque') {
    const relatorio = dados as RelatorioEstoqueOut;
    return (
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Código</th>
              <th>Item</th>
              <th>Categoria</th>
              <th className="num">Estoque Atual</th>
              <th className="num">Estoque Mínimo</th>
              <th>Situação</th>
            </tr>
          </thead>
          <tbody>
            {relatorio.itens.length === 0 && (
              <tr>
                <td colSpan={6} className="vazio-tabela">
                  Nenhum item no catálogo.
                </td>
              </tr>
            )}
            {relatorio.itens.map((item) => (
              <tr key={item.item_id}>
                <td className="mono">{item.codigo}</td>
                <td>{item.nome}</td>
                <td>{labelCategoriaItem(item.categoria)}</td>
                <td className="num">{item.estoque_atual}</td>
                <td className="num">{item.estoque_minimo}</td>
                <td>{item.critico ? <span className="pill danger">crítico</span> : <span className="pill ok">ok</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  if (aba === 'vencimentos') {
    const relatorio = dados as RelatorioVencimentosOut;
    return (
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Item</th>
              <th>Nº Lote</th>
              <th>Validade</th>
              <th className="num">Qtd. Atual</th>
              <th className="num">Dias p/ Vencer</th>
              <th>Situação</th>
            </tr>
          </thead>
          <tbody>
            {relatorio.itens.length === 0 && (
              <tr>
                <td colSpan={6} className="vazio-tabela">
                  Nenhum lote vencendo no período considerado.
                </td>
              </tr>
            )}
            {relatorio.itens.map((item) => (
              <tr key={item.lote_id}>
                <td>{item.item_nome}</td>
                <td className="mono">{item.numero_lote ?? '—'}</td>
                <td>{formatarData(item.data_validade)}</td>
                <td className="num">{item.quantidade_atual}</td>
                <td className="num">{item.dias_para_vencer}</td>
                <td>
                  <span className={`pill ${item.nivel === 'vencido' ? 'danger' : item.nivel === 'ate_30_dias' ? 'pend' : 'roxo'}`}>
                    {labelNivelVencimentoRelatorio(item.nivel)}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  const relatorio = dados as RelatorioMovimentacoesOut;
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Data/Hora</th>
            <th>Tipo</th>
            <th>Item</th>
            <th>Nº Lote</th>
            <th className="num">Quantidade</th>
            <th>Motivo Ajuste</th>
            <th>Usuário</th>
          </tr>
        </thead>
        <tbody>
          {relatorio.itens.length === 0 && (
            <tr>
              <td colSpan={7} className="vazio-tabela">
                Nenhuma movimentação encontrada com esse filtro.
              </td>
            </tr>
          )}
          {relatorio.itens.map((m) => (
            <tr key={m.id}>
              <td className="mono">{formatarDataHora(m.data_hora)}</td>
              <td>{labelTipoMovimentacao(m.tipo)}</td>
              <td>{m.lote.item.nome}</td>
              <td className="mono">{m.lote.numero_lote ?? '—'}</td>
              <td className="num">{m.quantidade}</td>
              <td>{m.motivo_ajuste ?? '—'}</td>
              <td>{m.usuario.nome}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
