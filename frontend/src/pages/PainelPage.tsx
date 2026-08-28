import { useCallback, useEffect, useMemo, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { api, baixarArquivo, mensagemErro } from '../lib/api';
import { Alerta } from '../components/Alerta';
import { BuscaAutocomplete } from '../components/BuscaAutocomplete';
import { formatarDataHora, labelStatusPedido, pillStatusPedido } from '../lib/formato';
import type { ConferirItemPayload, ItemOut, PedidoOut, Setor, StatusPedido } from '../types';

interface EdicaoItem {
  quantidade: string;
  liberar: boolean;
  /** Substituição — qualquer perfil pode entregar um item diferente do
   * solicitado quando o pedido é o que tem (ex.: pediram seringa com
   * rosca, só tem com bico). `motivoSubstituicao` é obrigatório quando
   * `itemSubstituto` está preenchido. */
  substituindo: boolean;
  itemSubstituto: ItemOut | null;
  buscaSubstituto: string;
  motivoSubstituicao: string;
}

type AbaStatus = 'todos' | StatusPedido;

function dataLocalISO(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  const ano = d.getFullYear();
  const mes = String(d.getMonth() + 1).padStart(2, '0');
  const dia = String(d.getDate()).padStart(2, '0');
  return `${ano}-${mes}-${dia}`;
}

function hojeISO(): string {
  return dataLocalISO(new Date().toISOString());
}

function itensResumoTexto(pedido: PedidoOut): string {
  return pedido.itens
    .map((it) => `${it.item_solicitado?.nome ?? `item #${it.item_id_solicitado}`} × ${it.quantidade_solicitada}`)
    .join('; ');
}

/** Painel do almoxarifado — fila de pedidos do formulário público, com
 * cards de resumo, abas de status, filtros, seleção em lote e
 * conferência item a item num modal. Layout inspirado no protótipo do
 * painel em planilha/Apps Script que o time já usava, adaptado à nossa
 * API (login/senha em vez de PIN, conferência real com baixa de estoque
 * via FEFO em vez de simulação client-side).
 *
 * Conferência: o item entregue é sempre o item solicitado (o quadro já
 * identifica o material — sem seletor de troca de item aqui; uma
 * eventual substituição é assunto do Ajuste de Estoque, não desta
 * tela). Cada item tem quantidade solicitada (fixa) e quantidade
 * dispensada (editável, até o limite do solicitado), com um checkbox
 * pra escolher quais itens estão sendo liberados nesta passada — dá pra
 * conferir só parte do pedido agora e voltar depois pro resto.
 *
 * Status do pedido: "pendente" (nada conferido), "parcial" (algum item
 * conferido, mas nem todos, OU todos conferidos com quantidade menor
 * que a solicitada) e "executado" (tudo conferido na quantidade cheia)
 * — calculado pelo backend a cada conferência.
 *
 * "Marcar Executado (sem conferência)" reaproveita
 * `POST /pedidos/{id}/executar-direto` — ainda dá baixa real de estoque
 * (entrega = solicitado), só pula a tela item a item. Não existe
 * "Reabrir": o backend não tem rota para desfazer uma conferência (isso
 * exigiria estornar a baixa de estoque já feita), então essa ação do
 * protótipo original não foi replicada. */
export function PainelPage() {
  const { token } = useAuth();

  const [setores, setSetores] = useState<Setor[]>([]);
  const [catalogo, setCatalogo] = useState<ItemOut[]>([]);
  const [pedidos, setPedidos] = useState<PedidoOut[]>([]);
  const [carregandoLista, setCarregandoLista] = useState(true);
  const [erroLista, setErroLista] = useState<string | null>(null);
  const [avisoLista, setAvisoLista] = useState<string | null>(null);
  const [ultimaAtualizacao, setUltimaAtualizacao] = useState<Date | null>(null);

  const [aba, setAba] = useState<AbaStatus>('todos');
  const [busca, setBusca] = useState('');
  const [setorFiltro, setSetorFiltro] = useState('');
  const [dataFiltro, setDataFiltro] = useState('');

  const [selecionados, setSelecionados] = useState<Set<number>>(new Set());
  const [executandoLote, setExecutandoLote] = useState(false);

  useEffect(() => {
    if (!token) return;
    api.get<Setor[]>('/setores', { token }).then(setSetores).catch(() => {});
    // Catálogo completo — só usado pra buscar um item substituto na
    // conferência (ver EdicaoItem.itemSubstituto).
    api.get<ItemOut[]>('/itens', { token }).then(setCatalogo).catch(() => {});
  }, [token]);

  const carregarLista = useCallback(() => {
    if (!token) return;
    setCarregandoLista(true);
    setErroLista(null);
    api
      .get<PedidoOut[]>('/pedidos', { token })
      .then((dados) => {
        setPedidos(dados);
        setUltimaAtualizacao(new Date());
      })
      .catch((err) => setErroLista(mensagemErro(err, 'Não foi possível carregar a fila de pedidos.')))
      .finally(() => setCarregandoLista(false));
  }, [token]);

  useEffect(() => {
    carregarLista();
  }, [carregarLista]);

  const resumo = useMemo(() => {
    const total = pedidos.length;
    const pendentes = pedidos.filter((p) => p.status === 'pendente').length;
    const parciais = pedidos.filter((p) => p.status === 'parcial').length;
    const executados = pedidos.filter((p) => p.status === 'executado').length;
    const hoje = new Date().toDateString();
    const recebidosHoje = pedidos.filter((p) => new Date(p.data_hora).toDateString() === hoje).length;
    return { total, pendentes, parciais, executados, recebidosHoje };
  }, [pedidos]);

  const listaFiltrada = useMemo(() => {
    const termo = busca.trim().toLowerCase();
    return pedidos.filter((p) => {
      if (aba !== 'todos' && p.status !== aba) return false;
      if (setorFiltro && String(p.setor_id) !== setorFiltro) return false;
      if (dataFiltro && dataLocalISO(p.data_hora) !== dataFiltro) return false;
      if (termo) {
        const alvo = [String(p.id), p.setor?.nome ?? '', p.responsavel_solicitante, itensResumoTexto(p)]
          .join(' ')
          .toLowerCase();
        if (!alvo.includes(termo)) return false;
      }
      return true;
    });
  }, [pedidos, aba, setorFiltro, dataFiltro, busca]);

  // ---- seleção em lote (só pedidos ainda não totalmente conferidos) ----
  const selecionaveisVisiveis = useMemo(
    () => listaFiltrada.filter((p) => p.status !== 'executado').map((p) => p.id),
    [listaFiltrada],
  );
  const todosMarcados = selecionaveisVisiveis.length > 0 && selecionaveisVisiveis.every((id) => selecionados.has(id));

  function alternarSelecao(id: number, marcado: boolean) {
    setSelecionados((atual) => {
      const novo = new Set(atual);
      if (marcado) novo.add(id);
      else novo.delete(id);
      return novo;
    });
  }

  function alternarTodos(marcarTodos: boolean) {
    setSelecionados((atual) => {
      const novo = new Set(atual);
      selecionaveisVisiveis.forEach((id) => {
        if (marcarTodos) novo.add(id);
        else novo.delete(id);
      });
      return novo;
    });
  }

  async function executarSelecionadosSemConferencia() {
    if (selecionados.size === 0) return;
    if (
      !confirm(
        `Marcar ${selecionados.size} pedido(s) como executado, entregando exatamente o que foi solicitado (sem conferência item a item)?`,
      )
    ) {
      return;
    }
    setExecutandoLote(true);
    setErroLista(null);
    setAvisoLista(null);
    const ids = Array.from(selecionados);
    const falhas: number[] = [];
    for (const id of ids) {
      try {
        await api.post(`/pedidos/${id}/executar-direto`, undefined, { token });
      } catch {
        falhas.push(id);
      }
    }
    setSelecionados(new Set());
    setExecutandoLote(false);
    carregarLista();
    if (falhas.length > 0) {
      setAvisoLista(
        `Não foi possível executar direto o(s) pedido(s) #${falhas.join(', #')} — provavelmente estoque insuficiente para algum item. Confira item a item.`,
      );
    }
  }

  // ---- modal de conferência ----
  const [pedidoModalId, setPedidoModalId] = useState<number | null>(null);
  const [detalhe, setDetalhe] = useState<PedidoOut | null>(null);
  const [carregandoDetalhe, setCarregandoDetalhe] = useState(false);
  const [erroDetalhe, setErroDetalhe] = useState<string | null>(null);
  const [edicoes, setEdicoes] = useState<Record<number, EdicaoItem>>({});
  const [confirmando, setConfirmando] = useState(false);

  function abrirModal(id: number) {
    setPedidoModalId(id);
    setErroDetalhe(null);
    setDetalhe(null);
    setCarregandoDetalhe(true);
    api
      .get<PedidoOut>(`/pedidos/${id}`, { token })
      .then((dados) => {
        setDetalhe(dados);
        setEdicoes(
          Object.fromEntries(
            dados.itens
              .filter((it) => it.item_id_entregue == null)
              .map((it) => [
                it.id,
                {
                  quantidade: String(it.quantidade_solicitada),
                  liberar: true,
                  substituindo: false,
                  itemSubstituto: null,
                  buscaSubstituto: '',
                  motivoSubstituicao: '',
                },
              ]),
          ),
        );
      })
      .catch((err) => setErroDetalhe(mensagemErro(err, 'Não foi possível carregar o pedido.')))
      .finally(() => setCarregandoDetalhe(false));
  }

  function fecharModal() {
    setPedidoModalId(null);
    setDetalhe(null);
    setEdicoes({});
    setErroDetalhe(null);
  }

  const todosItensConferidos = detalhe != null && detalhe.itens.every((it) => it.item_id_entregue != null);

  async function confirmarItensMarcados() {
    if (!detalhe) return;
    const itensParaEnviar = detalhe.itens.filter((it) => it.item_id_entregue == null && edicoes[it.id]?.liberar);

    if (itensParaEnviar.length === 0) {
      setErroDetalhe('Marque ao menos um item para liberar (ou cancele).');
      return;
    }

    for (const it of itensParaEnviar) {
      const quantidade = Number(edicoes[it.id].quantidade);
      const nome = it.item_solicitado?.nome ?? `item #${it.item_id_solicitado}`;
      if (Number.isNaN(quantidade) || quantidade < 0) {
        setErroDetalhe(`Informe uma quantidade dispensada válida para "${nome}".`);
        return;
      }
      if (quantidade > it.quantidade_solicitada) {
        setErroDetalhe(`A quantidade dispensada de "${nome}" não pode ser maior que a solicitada (${it.quantidade_solicitada}).`);
        return;
      }
      if (edicoes[it.id].substituindo) {
        if (!edicoes[it.id].itemSubstituto) {
          setErroDetalhe(`Escolha o item que está sendo entregue no lugar de "${nome}" (ou cancele a substituição).`);
          return;
        }
        if (!edicoes[it.id].motivoSubstituicao.trim()) {
          setErroDetalhe(`Informe o motivo da substituição de "${nome}".`);
          return;
        }
      }
    }

    setErroDetalhe(null);
    setConfirmando(true);
    try {
      for (const it of itensParaEnviar) {
        const edicao = edicoes[it.id];
        const payload: ConferirItemPayload = { quantidade_entregue: Number(edicao.quantidade) };
        if (edicao.substituindo && edicao.itemSubstituto) {
          payload.item_id_entregue = edicao.itemSubstituto.id;
          payload.motivo_substituicao = edicao.motivoSubstituicao.trim();
        }
        // eslint-disable-next-line no-await-in-loop -- confirmação sequencial de propósito (cada item é uma chamada própria da API)
        await api.patch(`/pedidos/${detalhe.id}/itens/${it.id}/conferir`, payload, { token });
      }
      fecharModal();
      carregarLista();
    } catch (err) {
      setErroDetalhe(mensagemErro(err, 'Não foi possível confirmar os itens marcados. Os itens já confirmados antes do erro foram salvos.'));
      abrirModal(detalhe.id);
    } finally {
      setConfirmando(false);
    }
  }

  // ---- relatório gerencial rápido (saídas executadas) ----
  const [relDe, setRelDe] = useState('');
  const [relAte, setRelAte] = useState('');
  const [exportando, setExportando] = useState<'pdf' | 'excel' | null>(null);

  async function exportarRelatorio(formato: 'pdf' | 'excel') {
    setExportando(formato);
    setErroLista(null);
    try {
      await baixarArquivo('/relatorios/pedidos', {
        token,
        params: { formato, status: 'executado', data_inicio: relDe || undefined, data_fim: relAte || undefined },
      });
    } catch (err) {
      setErroLista(mensagemErro(err, 'Não foi possível gerar o relatório.'));
    } finally {
      setExportando(null);
    }
  }

  return (
    <section>
      <div className="screen-head">
        <h1>Painel do almoxarifado</h1>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          {ultimaAtualizacao && (
            <span className="screen-tag">Atualizado às {ultimaAtualizacao.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}</span>
          )}
          <button type="button" className="btn ghost sm" disabled={carregandoLista} onClick={carregarLista}>
            {carregandoLista ? 'Atualizando…' : 'Atualizar'}
          </button>
        </div>
      </div>
      <p className="screen-sub">Fila de pedidos feitos pelo formulário público. Confira item a item para liberar, ou marque em lote.</p>

      {erroLista && <Alerta tipo="erro">{erroLista}</Alerta>}
      {avisoLista && <Alerta tipo="info">{avisoLista}</Alerta>}

      <div className="tiles">
        <div className="tile">
          <div className="k">Total de pedidos</div>
          <div className="v">{carregandoLista ? '—' : resumo.total}</div>
        </div>
        <div className="tile">
          <div className="k">Pendentes</div>
          <div className={`v ${resumo.pendentes > 0 ? 'warn' : ''}`}>{carregandoLista ? '—' : resumo.pendentes}</div>
        </div>
        <div className="tile">
          <div className="k">Parciais</div>
          <div className="v">{carregandoLista ? '—' : resumo.parciais}</div>
        </div>
        <div className="tile">
          <div className="k">Executados</div>
          <div className="v">{carregandoLista ? '—' : resumo.executados}</div>
        </div>
        <div className="tile">
          <div className="k">Recebidos hoje</div>
          <div className="v">{carregandoLista ? '—' : resumo.recebidosHoje}</div>
        </div>
      </div>

      <div className="tabs2" role="tablist">
        {(['todos', 'pendente', 'parcial', 'executado'] as AbaStatus[]).map((valor) => (
          <button key={valor} type="button" role="tab" className="tab2" aria-selected={aba === valor} onClick={() => setAba(valor)}>
            {valor === 'todos' ? 'Todos' : labelStatusPedido(valor)}
          </button>
        ))}
      </div>

      <div className="panel">
        <div className="grid g3" style={{ marginBottom: 0 }}>
          <div className="field">
            <label htmlFor="filtro-data">Data da solicitação</label>
            <div style={{ display: 'flex', gap: 6 }}>
              <input id="filtro-data" type="date" value={dataFiltro} onChange={(e) => setDataFiltro(e.target.value)} />
              <button type="button" className="btn ghost sm" onClick={() => setDataFiltro(hojeISO())}>
                Hoje
              </button>
              <button type="button" className="btn ghost sm" onClick={() => setDataFiltro('')}>
                Todas
              </button>
            </div>
          </div>
          <div className="field">
            <label htmlFor="filtro-busca">Buscar</label>
            <input
              id="filtro-busca"
              type="text"
              placeholder="ID, setor, responsável ou item…"
              value={busca}
              onChange={(e) => setBusca(e.target.value)}
            />
          </div>
          <div className="field">
            <label htmlFor="filtro-setor">Setor</label>
            <select id="filtro-setor" value={setorFiltro} onChange={(e) => setSetorFiltro(e.target.value)}>
              <option value="">Todos os setores</option>
              {setores.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.nome}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {selecionados.size > 0 && (
        <div className="barra-lote">
          <span>
            {selecionados.size} {selecionados.size === 1 ? 'selecionado' : 'selecionados'}
          </span>
          <div className="barra-lote-botoes">
            <button type="button" className="btn sm" disabled={executandoLote} onClick={executarSelecionadosSemConferencia}>
              {executandoLote ? 'Executando…' : 'Marcar executado (sem conferência)'}
            </button>
            <button type="button" className="btn ghost sm" onClick={() => setSelecionados(new Set())}>
              Limpar seleção
            </button>
          </div>
        </div>
      )}

      <div className="panel">
        {carregandoLista && <p className="carregando">Carregando…</p>}
        {!carregandoLista && (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th className="chk-col">
                    <input
                      type="checkbox"
                      checked={todosMarcados}
                      disabled={selecionaveisVisiveis.length === 0}
                      onChange={(e) => alternarTodos(e.target.checked)}
                    />
                  </th>
                  <th>#</th>
                  <th>Data/hora</th>
                  <th>Setor</th>
                  <th>Responsável</th>
                  <th>Itens solicitados</th>
                  <th>Status</th>
                  <th>Ação</th>
                </tr>
              </thead>
              <tbody>
                {listaFiltrada.length === 0 && (
                  <tr>
                    <td colSpan={8} className="vazio-tabela">
                      Nenhum pedido encontrado com esse filtro.
                    </td>
                  </tr>
                )}
                {listaFiltrada.map((p) => {
                  const executado = p.status === 'executado';
                  return (
                    <tr key={p.id} className={selecionados.has(p.id) ? 'selecionada' : ''}>
                      <td>
                        {!executado && (
                          <input
                            type="checkbox"
                            checked={selecionados.has(p.id)}
                            onChange={(e) => alternarSelecao(p.id, e.target.checked)}
                          />
                        )}
                      </td>
                      <td className="mono">#{p.id}</td>
                      <td className="mono">{formatarDataHora(p.data_hora)}</td>
                      <td>{p.setor?.nome ?? setores.find((s) => s.id === p.setor_id)?.nome ?? `#${p.setor_id}`}</td>
                      <td>{p.responsavel_solicitante}</td>
                      <td className="itens-resumo">
                        {itensResumoTexto(p)}
                        {p.observacao && <div className="obs">Obs: {p.observacao}</div>}
                      </td>
                      <td>
                        <span className={pillStatusPedido(p.status)}>{labelStatusPedido(p.status)}</span>
                        {p.data_execucao && (
                          <div className="obs" style={{ marginTop: 4 }}>
                            {formatarDataHora(p.data_execucao)}
                            {p.usuario_execucao && ` — ${p.usuario_execucao.nome}`}
                          </div>
                        )}
                      </td>
                      <td>
                        <div className="acoes-linha">
                          <button type="button" className="btn ghost sm" onClick={() => abrirModal(p.id)}>
                            {executado ? 'Ver detalhes' : 'Conferir e liberar'}
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="panel">
        <h2>Relatório gerencial de saídas</h2>
        <div className="grid g3" style={{ marginBottom: 0 }}>
          <div className="field">
            <label htmlFor="rel-de">De</label>
            <input id="rel-de" type="date" value={relDe} onChange={(e) => setRelDe(e.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="rel-ate">Até</label>
            <input id="rel-ate" type="date" value={relAte} onChange={(e) => setRelAte(e.target.value)} />
          </div>
          <div className="field" style={{ justifyContent: 'flex-end', flexDirection: 'row', gap: 10 }}>
            <button type="button" className="btn ghost" disabled={exportando !== null} onClick={() => exportarRelatorio('excel')}>
              {exportando === 'excel' ? 'Gerando…' : 'Gerar Excel'}
            </button>
            <button type="button" className="btn ghost" disabled={exportando !== null} onClick={() => exportarRelatorio('pdf')}>
              {exportando === 'pdf' ? 'Gerando…' : 'Gerar PDF'}
            </button>
          </div>
        </div>
        <p className="note" style={{ marginTop: 16 }}>
          Considera apenas pedidos <strong>executados</strong>, filtrando pela data da solicitação.
        </p>
      </div>

      {pedidoModalId != null && (
        <div className="modal-overlay" onClick={fecharModal}>
          <div className="modal-box" onClick={(e) => e.stopPropagation()}>
            {carregandoDetalhe && <p className="carregando">Carregando…</p>}
            {!carregandoDetalhe && detalhe && (
              <>
                <h2>{todosItensConferidos ? 'Detalhes da entrega' : 'Conferir itens do pedido'}</h2>
                <div className="sub">
                  Pedido #{detalhe.id} — {detalhe.setor?.nome ?? `#${detalhe.setor_id}`} — {detalhe.responsavel_solicitante}
                </div>

                {todosItensConferidos && (
                  <Alerta tipo="info">Todos os itens deste pedido já foram conferidos — exibindo apenas o que foi registrado (somente leitura).</Alerta>
                )}
                {erroDetalhe && <Alerta tipo="erro">{erroDetalhe}</Alerta>}

                {detalhe.itens.map((it) => {
                  const nome = it.item_solicitado?.nome ?? `item #${it.item_id_solicitado}`;
                  const jaConferido = it.item_id_entregue != null;

                  if (jaConferido) {
                    const parcial = (it.quantidade_entregue ?? 0) < it.quantidade_solicitada;
                    const substituido = it.item_id_entregue != null && it.item_id_entregue !== it.item_id_solicitado;
                    return (
                      <div key={it.id} className="item-conferencia">
                        <div className="titulo-item">
                          {nome} <span className="qtd-pedida">(solicitado: {it.quantidade_solicitada})</span>
                        </div>
                        <p className={`note ${parcial ? '' : 'ok'}`} style={{ marginTop: 0 }}>
                          Dispensado: <strong>{it.quantidade_entregue}</strong> de {it.quantidade_solicitada}
                          {it.quantidade_entregue === 0 && ' — não atendido'}
                          {parcial && it.quantidade_entregue !== 0 && ' — entrega parcial'}
                        </p>
                        {substituido && (
                          <p className="note" style={{ marginTop: 4 }}>
                            Substituído por <strong>{it.item_entregue?.nome ?? `item #${it.item_id_entregue}`}</strong>
                            {it.motivo_substituicao && <> — motivo: {it.motivo_substituicao}</>}
                          </p>
                        )}
                      </div>
                    );
                  }

                  const edicao = edicoes[it.id];
                  if (!edicao) return null;
                  return (
                    <div key={it.id} className="item-conferencia">
                      <label className="titulo-item item-conferencia-checkbox">
                        <input
                          type="checkbox"
                          checked={edicao.liberar}
                          onChange={(e) => setEdicoes((atual) => ({ ...atual, [it.id]: { ...atual[it.id], liberar: e.target.checked } }))}
                        />
                        {nome}
                      </label>
                      <div className="grid">
                        <div className="field">
                          <label>Qtd. solicitada</label>
                          <div className="box">{it.quantidade_solicitada}</div>
                        </div>
                        <div className="field">
                          <label>Qtd. dispensada</label>
                          <input
                            type="number"
                            min={0}
                            max={it.quantidade_solicitada}
                            disabled={!edicao.liberar}
                            value={edicao.quantidade}
                            onChange={(e) => setEdicoes((atual) => ({ ...atual, [it.id]: { ...atual[it.id], quantidade: e.target.value } }))}
                          />
                        </div>
                      </div>

                      <button
                        type="button"
                        className="link-btn"
                        style={{ marginTop: 6 }}
                        onClick={() =>
                          setEdicoes((atual) => ({
                            ...atual,
                            [it.id]: atual[it.id].substituindo
                              ? { ...atual[it.id], substituindo: false, itemSubstituto: null, buscaSubstituto: '', motivoSubstituicao: '' }
                              : { ...atual[it.id], substituindo: true },
                          }))
                        }
                      >
                        {edicao.substituindo ? '✕ Cancelar substituição' : '⇄ Entregar outro item (substituição)'}
                      </button>

                      {edicao.substituindo && (
                        <div className="grid" style={{ marginTop: 8 }}>
                          <div className="field">
                            <label>Item que está sendo entregue</label>
                            <BuscaAutocomplete
                              itens={catalogo.filter((i) => i.ativo)}
                              valor={edicao.buscaSubstituto}
                              aoMudarValor={(v) =>
                                setEdicoes((atual) => ({ ...atual, [it.id]: { ...atual[it.id], buscaSubstituto: v, itemSubstituto: null } }))
                              }
                              rotulo={(i) => `${i.codigo} — ${i.nome}`}
                              chave={(i) => i.id}
                              aoSelecionar={(i) =>
                                setEdicoes((atual) => ({
                                  ...atual,
                                  [it.id]: { ...atual[it.id], itemSubstituto: i, buscaSubstituto: `${i.codigo} — ${i.nome}` },
                                }))
                              }
                              placeholder="Código ou nome do item…"
                            />
                          </div>
                          <div className="field">
                            <label>Motivo da substituição</label>
                            <input
                              type="text"
                              placeholder="ex.: só tem seringa com bico, não com rosca"
                              value={edicao.motivoSubstituicao}
                              onChange={(e) =>
                                setEdicoes((atual) => ({ ...atual, [it.id]: { ...atual[it.id], motivoSubstituicao: e.target.value } }))
                              }
                            />
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}

                <div className="modal-botoes">
                  <button type="button" className="btn ghost" onClick={fecharModal}>
                    {todosItensConferidos ? 'Fechar' : 'Cancelar'}
                  </button>
                  {!todosItensConferidos && (
                    <button type="button" className="btn" disabled={confirmando} onClick={confirmarItensMarcados}>
                      {confirmando ? 'Confirmando…' : 'Confirmar itens marcados'}
                    </button>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
