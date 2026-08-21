import { useCallback, useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { api, mensagemErro } from '../lib/api';
import { Alerta } from '../components/Alerta';
import { formatarDataHora, labelStatusPedido, pillStatusPedido } from '../lib/formato';
import type { ConferirItemPayload, ItemOut, PedidoOut, Setor, StatusPedido } from '../types';

interface EdicaoItem {
  itemEntregueId: number;
  quantidade: string;
  motivo: string;
}

/** Fila de pedidos do formulário público. Cada pedido tem N itens,
 * conferidos individualmente (lote sugerido/qualquer atendente confirma
 * a quantidade entregue, com opção de substituir por outro item do
 * catálogo — motivo obrigatório nesse caso). O pedido fecha
 * ("executado") só quando todos os itens forem conferidos — quem decide
 * isso é o backend; o front só reflete o `status` retornado após cada
 * confirmação.
 *
 * Rota de conferência (`PATCH /pedidos/{id}/itens/{itemId}/conferir`) é
 * uma inferência a partir do fluxo descrito no doc — não fixada
 * literalmente pelo contrato recebido. Ver nota em src/types.ts. */
export function PainelPage() {
  const { token } = useAuth();

  const [setores, setSetores] = useState<Setor[]>([]);
  const [catalogo, setCatalogo] = useState<ItemOut[]>([]);
  const [pedidos, setPedidos] = useState<PedidoOut[]>([]);
  const [carregandoLista, setCarregandoLista] = useState(true);
  const [erroLista, setErroLista] = useState<string | null>(null);

  const [statusFiltro, setStatusFiltro] = useState<StatusPedido | ''>('pendente');
  const [setorFiltro, setSetorFiltro] = useState('');

  useEffect(() => {
    if (!token) return;
    api.get<Setor[]>('/setores', { token }).then(setSetores).catch(() => {});
    api.get<ItemOut[]>('/itens', { token }).then(setCatalogo).catch(() => {});
  }, [token]);

  const carregarLista = useCallback(() => {
    if (!token) return;
    setCarregandoLista(true);
    setErroLista(null);
    api
      .get<PedidoOut[]>('/pedidos', { token, params: { status: statusFiltro || undefined, setor_id: setorFiltro || undefined } })
      .then(setPedidos)
      .catch((err) => setErroLista(mensagemErro(err, 'Não foi possível carregar a fila de pedidos.')))
      .finally(() => setCarregandoLista(false));
  }, [token, statusFiltro, setorFiltro]);

  useEffect(() => {
    carregarLista();
  }, [carregarLista]);

  // ---- detalhe/conferência ----
  const [selecionadoId, setSelecionadoId] = useState<number | null>(null);
  const [detalhe, setDetalhe] = useState<PedidoOut | null>(null);
  const [carregandoDetalhe, setCarregandoDetalhe] = useState(false);
  const [erroDetalhe, setErroDetalhe] = useState<string | null>(null);
  const [edicoes, setEdicoes] = useState<Record<number, EdicaoItem>>({});
  const [conferindoItemId, setConferindoItemId] = useState<number | null>(null);

  const carregarDetalhe = useCallback(
    (id: number) => {
      if (!token) return;
      setCarregandoDetalhe(true);
      setErroDetalhe(null);
      api
        .get<PedidoOut>(`/pedidos/${id}`, { token })
        .then((dados) => {
          setDetalhe(dados);
          setEdicoes(
            Object.fromEntries(
              dados.itens.map((it) => [
                it.id,
                {
                  itemEntregueId: it.item_id_entregue ?? it.item_id_solicitado,
                  quantidade: String(it.quantidade_entregue ?? it.quantidade_solicitada),
                  motivo: it.motivo_substituicao ?? '',
                },
              ]),
            ),
          );
        })
        .catch((err) => setErroDetalhe(mensagemErro(err, 'Não foi possível carregar o pedido.')))
        .finally(() => setCarregandoDetalhe(false));
    },
    [token],
  );

  function selecionarPedido(id: number) {
    setSelecionadoId(id);
    carregarDetalhe(id);
  }

  async function confirmarItem(pedidoItemId: number, itemSolicitadoId: number) {
    const edicao = edicoes[pedidoItemId];
    if (!edicao || !detalhe) return;

    const substituindo = edicao.itemEntregueId !== itemSolicitadoId;
    if (substituindo && !edicao.motivo.trim()) {
      setErroDetalhe('Informe o motivo da substituição antes de confirmar.');
      return;
    }
    const quantidade = Number(edicao.quantidade);
    if (!quantidade || quantidade <= 0) {
      setErroDetalhe('Informe uma quantidade entregue válida.');
      return;
    }

    setErroDetalhe(null);
    setConferindoItemId(pedidoItemId);
    const payload: ConferirItemPayload = {
      quantidade_entregue: quantidade,
      ...(substituindo ? { item_id_entregue: edicao.itemEntregueId, motivo_substituicao: edicao.motivo.trim() } : {}),
    };
    try {
      await api.patch(`/pedidos/${detalhe.id}/itens/${pedidoItemId}/conferir`, payload, { token });
      carregarDetalhe(detalhe.id);
      carregarLista();
    } catch (err) {
      setErroDetalhe(mensagemErro(err, 'Não foi possível confirmar este item.'));
    } finally {
      setConferindoItemId(null);
    }
  }

  return (
    <section>
      <div className="screen-head">
        <h1>Painel de pedidos</h1>
        <span className="screen-tag">conferência</span>
      </div>
      <p className="screen-sub">Fila de pedidos feitos pelo formulário público. Confira item a item para liberar.</p>

      {erroLista && <Alerta tipo="erro">{erroLista}</Alerta>}

      <div className="panel">
        <div className="grid g3" style={{ marginBottom: 0 }}>
          <div className="field">
            <label htmlFor="filtro-status">Status</label>
            <select id="filtro-status" value={statusFiltro} onChange={(e) => setStatusFiltro(e.target.value as StatusPedido | '')}>
              <option value="">Todos</option>
              <option value="pendente">Pendente</option>
              <option value="executado">Executado</option>
            </select>
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

      <div className="lista-detalhe">
        <div className="panel">
          <h2>Pedidos</h2>
          {carregandoLista && <p className="carregando">Carregando…</p>}
          {!carregandoLista && (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Setor</th>
                    <th>Responsável</th>
                    <th>Data/hora</th>
                    <th>Itens</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {pedidos.length === 0 && (
                    <tr>
                      <td colSpan={6} className="vazio-tabela">
                        Nenhum pedido encontrado.
                      </td>
                    </tr>
                  )}
                  {pedidos.map((p) => (
                    <tr
                      key={p.id}
                      className={`clicavel ${selecionadoId === p.id ? 'selecionada' : ''}`}
                      onClick={() => selecionarPedido(p.id)}
                    >
                      <td className="mono">#{p.id}</td>
                      <td>{p.setor?.nome ?? setores.find((s) => s.id === p.setor_id)?.nome ?? `#${p.setor_id}`}</td>
                      <td>{p.responsavel_solicitante}</td>
                      <td className="mono">{formatarDataHora(p.data_hora)}</td>
                      <td className="num">{p.itens?.length ?? '—'}</td>
                      <td>
                        <span className={pillStatusPedido(p.status)}>{labelStatusPedido(p.status)}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="panel">
          <h2>Detalhe</h2>
          {selecionadoId == null && <p className="carregando">Selecione um pedido na lista ao lado.</p>}
          {selecionadoId != null && carregandoDetalhe && <p className="carregando">Carregando…</p>}
          {erroDetalhe && <Alerta tipo="erro">{erroDetalhe}</Alerta>}
          {selecionadoId != null && !carregandoDetalhe && detalhe && (
            <>
              <div className="detalhe-linha">
                <span className="k">Protocolo</span>
                <span className="v mono">#{detalhe.id}</span>
              </div>
              <div className="detalhe-linha">
                <span className="k">Setor</span>
                <span className="v">{detalhe.setor?.nome ?? setores.find((s) => s.id === detalhe.setor_id)?.nome ?? '—'}</span>
              </div>
              <div className="detalhe-linha">
                <span className="k">Responsável</span>
                <span className="v">{detalhe.responsavel_solicitante}</span>
              </div>
              <div className="detalhe-linha">
                <span className="k">Data/hora</span>
                <span className="v mono">{formatarDataHora(detalhe.data_hora)}</span>
              </div>
              {detalhe.observacao && (
                <div className="detalhe-linha">
                  <span className="k">Observação</span>
                  <span className="v">{detalhe.observacao}</span>
                </div>
              )}
              <div className="detalhe-linha">
                <span className="k">Status</span>
                <span className={pillStatusPedido(detalhe.status)}>{labelStatusPedido(detalhe.status)}</span>
              </div>

              <div style={{ marginTop: 16 }}>
                {detalhe.itens.map((it) => {
                  const conferido = it.item_id_entregue != null;
                  const edicao = edicoes[it.id];
                  return (
                    <div key={it.id} className="panel" style={{ background: 'var(--surface-2)', boxShadow: 'none' }}>
                      <h2 style={{ marginBottom: 8 }}>
                        {it.item_solicitado?.nome ?? `Item #${it.item_id_solicitado}`} — pedido: {it.quantidade_solicitada}
                      </h2>
                      {conferido ? (
                        <p className="note ok" style={{ marginTop: 0 }}>
                          Entregue: <strong>{it.item_entregue?.nome ?? it.item_id_entregue}</strong> × {it.quantidade_entregue}
                          {it.motivo_substituicao && (
                            <>
                              {' '}
                              — substituição: {it.motivo_substituicao}
                            </>
                          )}
                        </p>
                      ) : (
                        edicao && (
                          <div className="grid g3">
                            <div className="field">
                              <label>Item entregue</label>
                              <select
                                value={edicao.itemEntregueId}
                                onChange={(e) =>
                                  setEdicoes((atual) => ({
                                    ...atual,
                                    [it.id]: { ...atual[it.id], itemEntregueId: Number(e.target.value) },
                                  }))
                                }
                              >
                                <option value={it.item_id_solicitado}>
                                  {it.item_solicitado?.nome ?? 'Item solicitado'} (solicitado)
                                </option>
                                {catalogo
                                  .filter((c) => c.id !== it.item_id_solicitado)
                                  .map((c) => (
                                    <option key={c.id} value={c.id}>
                                      {c.nome} (saldo {c.estoque_atual})
                                    </option>
                                  ))}
                              </select>
                            </div>
                            <div className="field">
                              <label>Qtd. entregue</label>
                              <input
                                type="number"
                                min={0}
                                value={edicao.quantidade}
                                onChange={(e) =>
                                  setEdicoes((atual) => ({ ...atual, [it.id]: { ...atual[it.id], quantidade: e.target.value } }))
                                }
                              />
                            </div>
                            {edicao.itemEntregueId !== it.item_id_solicitado && (
                              <div className="field span2">
                                <label>
                                  Motivo da substituição <span className="req">*</span>
                                </label>
                                <input
                                  type="text"
                                  value={edicao.motivo}
                                  onChange={(e) =>
                                    setEdicoes((atual) => ({ ...atual, [it.id]: { ...atual[it.id], motivo: e.target.value } }))
                                  }
                                />
                              </div>
                            )}
                            <div className="actions" style={{ marginTop: 6 }}>
                              <button
                                type="button"
                                className="btn sm"
                                disabled={conferindoItemId === it.id}
                                onClick={() => confirmarItem(it.id, it.item_id_solicitado)}
                              >
                                {conferindoItemId === it.id ? 'Confirmando…' : 'Confirmar item'}
                              </button>
                            </div>
                          </div>
                        )
                      )}
                    </div>
                  );
                })}
              </div>
            </>
          )}
        </div>
      </div>
    </section>
  );
}
