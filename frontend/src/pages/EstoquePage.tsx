import { useCallback, useEffect, useMemo, useState } from 'react';
import type { FormEvent } from 'react';
import { useAuth } from '../context/AuthContext';
import { api, mensagemErro } from '../lib/api';
import { permissoesDe } from '../lib/permissoes';
import { Alerta } from '../components/Alerta';
import { CATEGORIAS_ITEM, diasAteVencer, formatarData, formatarMoeda, labelCategoriaItem, labelOrigemLote, nivelValidade } from '../lib/formato';
import type { AjusteCriarPayload, CategoriaItem, ItemCriarPayload, ItemOut, LoteAtualizarPayload, LoteOut } from '../types';

const FORM_ITEM_VAZIO = { codigo: '', nome: '', apresentacao: '', categoria: 'material_medico' as CategoriaItem, estoque_minimo: '0' };

/** Estoque do almoxarifado — catálogo de itens com saldo agregado (Σ
 * lotes), alerta de estoque crítico e vencimento em 4 grupos (vencido,
 * ≤30d, 30–60d, ok — mesma régua da farmácia). Registrar entrada de
 * lote não acontece mais avulso por item aqui — só pelas telas
 * "Entrada por Compra" e "Empréstimos/Permutas". Cadastro/edição de
 * item e Ajuste de estoque continuam exclusivos do Coordenador (matriz
 * da seção 3.3 do doc). */
export function EstoquePage() {
  const { usuario, matrizPermissoes, token } = useAuth();
  const permissoes = permissoesDe(usuario, matrizPermissoes);

  const [itens, setItens] = useState<ItemOut[]>([]);
  const [lotes, setLotes] = useState<LoteOut[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const [sucesso, setSucesso] = useState<string | null>(null);
  const [busca, setBusca] = useState('');
  const [mostrarInativos, setMostrarInativos] = useState(false);

  const carregar = useCallback(() => {
    if (!token) return;
    setCarregando(true);
    setErro(null);
    Promise.all([
      api.get<ItemOut[]>('/itens', { token, params: { incluir_inativos: mostrarInativos } }),
      api.get<LoteOut[]>('/lotes', { token }),
    ])
      .then(([itensResp, lotesResp]) => {
        setItens(itensResp);
        setLotes(lotesResp);
      })
      .catch((err) => setErro(mensagemErro(err, 'Não foi possível carregar o estoque.')))
      .finally(() => setCarregando(false));
  }, [token, mostrarInativos]);

  useEffect(() => {
    carregar();
  }, [carregar]);

  const itensFiltrados = useMemo(() => {
    const termo = busca.trim().toLowerCase();
    if (!termo) return itens;
    return itens.filter((i) => i.nome.toLowerCase().includes(termo) || i.codigo.toLowerCase().includes(termo));
  }, [itens, busca]);

  const itensCriticos = useMemo(
    () => itens.filter((i) => i.estoque_minimo > 0 && i.estoque_atual < i.estoque_minimo),
    [itens],
  );

  const lotesVencendo = useMemo(
    () =>
      lotes.filter((l) => {
        if (!l.data_validade) return false;
        const nivel = nivelValidade(diasAteVencer(l.data_validade));
        return nivel === 'vencido' || nivel === 'amarelo' || nivel === 'roxo';
      }),
    [lotes],
  );

  // ---- vencimento em 4 grupos (dashboard) ----
  const contagemVencimento = useMemo(() => {
    let vencidos = 0;
    let ate30 = 0;
    let entre30e60 = 0;
    let semUrgencia = 0;
    for (const l of lotes) {
      if (!l.data_validade) continue;
      switch (nivelValidade(diasAteVencer(l.data_validade))) {
        case 'vencido':
          vencidos++;
          break;
        case 'amarelo':
          ate30++;
          break;
        case 'roxo':
          entre30e60++;
          break;
        case 'ok':
          semUrgencia++;
          break;
      }
    }
    return { vencidos, ate30, entre30e60, semUrgencia };
  }, [lotes]);

  // ---- cadastro/edição de item (coordenador) ----
  const [editandoItemId, setEditandoItemId] = useState<number | null>(null);
  const [formItem, setFormItem] = useState(FORM_ITEM_VAZIO);
  const [salvandoItem, setSalvandoItem] = useState(false);

  function iniciarEdicaoItem(item: ItemOut) {
    setEditandoItemId(item.id);
    setFormItem({
      codigo: item.codigo,
      nome: item.nome,
      apresentacao: item.apresentacao ?? '',
      categoria: item.categoria,
      estoque_minimo: String(item.estoque_minimo),
    });
  }
  function cancelarEdicaoItem() {
    setEditandoItemId(null);
    setFormItem(FORM_ITEM_VAZIO);
  }

  async function aoSubmeterItem(e: FormEvent) {
    e.preventDefault();
    setErro(null);
    setSucesso(null);
    setSalvandoItem(true);
    const payload: ItemCriarPayload = {
      codigo: formItem.codigo.trim(),
      nome: formItem.nome.trim(),
      apresentacao: formItem.apresentacao.trim() || undefined,
      categoria: formItem.categoria,
      estoque_minimo: Number(formItem.estoque_minimo) || 0,
    };
    try {
      if (editandoItemId == null) {
        await api.post('/itens', payload, { token });
        setSucesso('Item cadastrado.');
      } else {
        await api.put(`/itens/${editandoItemId}`, payload, { token });
        setSucesso('Item atualizado.');
      }
      cancelarEdicaoItem();
      carregar();
    } catch (err) {
      setErro(mensagemErro(err, 'Não foi possível salvar o item.'));
    } finally {
      setSalvandoItem(false);
    }
  }

  async function alternarAtivoItem(item: ItemOut) {
    setErro(null);
    setSucesso(null);
    try {
      await api.put(`/itens/${item.id}`, { ativo: !item.ativo }, { token });
      setSucesso(item.ativo ? `${item.nome} desativado.` : `${item.nome} reativado.`);
      carregar();
    } catch (err) {
      setErro(mensagemErro(err, 'Não foi possível alterar o status do item.'));
    }
  }

  // ---- ajuste de estoque (coordenador) ----
  // O backend calcula o delta a partir do novo saldo informado contra o
  // saldo atual do lote — nunca aceita um delta pronto do cliente (mesmo
  // padrão da farmácia). O formulário pede "novo saldo" e só mostra a
  // diferença como apoio visual.
  const [loteAjuste, setLoteAjuste] = useState<LoteOut | null>(null);
  const [novoSaldoAjuste, setNovoSaldoAjuste] = useState('');
  const [motivoAjuste, setMotivoAjuste] = useState('');
  const [salvandoAjuste, setSalvandoAjuste] = useState(false);

  const diferencaAjuste = useMemo(() => {
    if (loteAjuste == null || novoSaldoAjuste.trim() === '') return null;
    return Number(novoSaldoAjuste) - loteAjuste.quantidade_atual;
  }, [loteAjuste, novoSaldoAjuste]);

  function abrirAjuste(lote: LoteOut) {
    setLoteAjuste(lote);
    setNovoSaldoAjuste(String(lote.quantidade_atual));
    setMotivoAjuste('');
    setErro(null);
    setSucesso(null);
  }

  async function aoSubmeterAjuste(e: FormEvent) {
    e.preventDefault();
    if (loteAjuste == null) return;
    setErro(null);
    setSucesso(null);
    setSalvandoAjuste(true);
    const payload: AjusteCriarPayload = {
      lote_id: loteAjuste.id,
      quantidade_nova: Number(novoSaldoAjuste),
      motivo_ajuste: motivoAjuste.trim(),
    };
    try {
      await api.post('/ajustes', payload, { token });
      setSucesso('Ajuste registrado.');
      setLoteAjuste(null);
      carregar();
    } catch (err) {
      setErro(mensagemErro(err, 'Não foi possível registrar o ajuste.'));
    } finally {
      setSalvandoAjuste(false);
    }
  }

  // ---- edição do valor unitário de um lote (correção pontual, gerenciarItens) ----
  const [loteEditandoValorId, setLoteEditandoValorId] = useState<number | null>(null);
  const [valorUnitarioEdit, setValorUnitarioEdit] = useState('');
  const [salvandoValorUnitario, setSalvandoValorUnitario] = useState(false);

  function abrirEdicaoValor(lote: LoteOut) {
    setLoteEditandoValorId(lote.id);
    setValorUnitarioEdit(lote.valor_unitario ?? '');
    setErro(null);
    setSucesso(null);
  }

  function cancelarEdicaoValor() {
    setLoteEditandoValorId(null);
    setValorUnitarioEdit('');
  }

  async function salvarValorUnitario(loteId: number) {
    setErro(null);
    setSucesso(null);
    setSalvandoValorUnitario(true);
    const payload: LoteAtualizarPayload = { valor_unitario: valorUnitarioEdit.trim() || null };
    try {
      await api.put(`/lotes/${loteId}`, payload, { token });
      setSucesso('Valor unitário atualizado.');
      cancelarEdicaoValor();
      carregar();
    } catch (err) {
      setErro(mensagemErro(err, 'Não foi possível atualizar o valor unitário.'));
    } finally {
      setSalvandoValorUnitario(false);
    }
  }

  return (
    <section>
      <div className="screen-head">
        <h1>Estoque</h1>
        <span className="screen-tag">catálogo e lotes</span>
      </div>
      <p className="screen-sub">Saldo agregado por item (soma dos lotes ativos), alerta de crítico e vencimento.</p>

      {erro && <Alerta tipo="erro">{erro}</Alerta>}
      {sucesso && <Alerta tipo="sucesso">{sucesso}</Alerta>}

      <div className="tiles">
        <div className="tile">
          <div className="k">Itens em estoque crítico</div>
          <div className={`v ${itensCriticos.length > 0 ? 'warn' : ''}`}>{carregando ? '—' : itensCriticos.length}</div>
        </div>
        <div className="tile">
          <div className="k">Lotes vencidos ou vencendo (60d)</div>
          <div className={`v ${lotesVencendo.length > 0 ? 'warn' : ''}`}>{carregando ? '—' : lotesVencendo.length}</div>
        </div>
        <div className="tile">
          <div className="k">Itens ativos no catálogo</div>
          <div className="v">{carregando ? '—' : itens.filter((i) => i.ativo).length}</div>
        </div>
      </div>

      <div className="tiles">
        <div className="tile">
          <div className="k">Vencidos</div>
          <div className={`v ${contagemVencimento.vencidos > 0 ? 'warn' : ''}`}>
            {carregando ? '—' : contagemVencimento.vencidos}
          </div>
        </div>
        <div className="tile">
          <div className="k">Vence em até 30 dias</div>
          <div className={`v ${contagemVencimento.ate30 > 0 ? 'warn' : ''}`}>
            {carregando ? '—' : contagemVencimento.ate30}
          </div>
        </div>
        <div className="tile">
          <div className="k">Vence em 30–60 dias</div>
          <div className={`v ${contagemVencimento.entre30e60 > 0 ? 'warn' : ''}`}>
            {carregando ? '—' : contagemVencimento.entre30e60}
          </div>
        </div>
        <div className="tile">
          <div className="k">Sem urgência (60+ dias)</div>
          <div className="v">{carregando ? '—' : contagemVencimento.semUrgencia}</div>
        </div>
      </div>

      {itensCriticos.length > 0 && (
        <div className="alerta-bloco alerta-critico">
          <h3>Estoque crítico</h3>
          <ul>
            {itensCriticos.map((i) => (
              <li key={i.id}>
                {i.nome} — {i.estoque_atual} / mínimo {i.estoque_minimo}
              </li>
            ))}
          </ul>
        </div>
      )}

      {permissoes.gerenciarItens && (
        <form className="panel" onSubmit={aoSubmeterItem}>
          <h2>{editandoItemId == null ? 'Novo item do catálogo' : `Editando — ${formItem.nome}`}</h2>
          <div className="grid">
            <div className="field">
              <label htmlFor="item-codigo">
                Código <span className="req">*</span>
              </label>
              <input
                id="item-codigo"
                type="text"
                value={formItem.codigo}
                onChange={(e) => setFormItem((f) => ({ ...f, codigo: e.target.value }))}
                required
              />
            </div>
            <div className="field">
              <label htmlFor="item-nome">
                Nome <span className="req">*</span>
              </label>
              <input
                id="item-nome"
                type="text"
                value={formItem.nome}
                onChange={(e) => setFormItem((f) => ({ ...f, nome: e.target.value }))}
                required
              />
            </div>
            <div className="field">
              <label htmlFor="item-apresentacao">
                Apresentação <span className="tag">opcional</span>
              </label>
              <input
                id="item-apresentacao"
                type="text"
                placeholder="ex.: Caixa c/ 100"
                value={formItem.apresentacao}
                onChange={(e) => setFormItem((f) => ({ ...f, apresentacao: e.target.value }))}
              />
            </div>
            <div className="field">
              <label htmlFor="item-categoria">
                Categoria <span className="req">*</span>
              </label>
              <select
                id="item-categoria"
                value={formItem.categoria}
                onChange={(e) => setFormItem((f) => ({ ...f, categoria: e.target.value as CategoriaItem }))}
                required
              >
                {CATEGORIAS_ITEM.map((c) => (
                  <option key={c} value={c}>
                    {labelCategoriaItem(c)}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label htmlFor="item-min">
                Estoque mínimo <span className="req">*</span>
              </label>
              <input
                id="item-min"
                type="number"
                min={0}
                value={formItem.estoque_minimo}
                onChange={(e) => setFormItem((f) => ({ ...f, estoque_minimo: e.target.value }))}
                required
              />
            </div>
          </div>
          <div className="actions">
            <button type="submit" className="btn" disabled={salvandoItem}>
              {salvandoItem ? 'Salvando…' : editandoItemId == null ? 'Cadastrar item' : 'Salvar alterações'}
            </button>
            {editandoItemId != null && (
              <button type="button" className="btn ghost" onClick={cancelarEdicaoItem}>
                Cancelar edição
              </button>
            )}
          </div>
        </form>
      )}

      {loteAjuste != null && (
        <form className="panel" onSubmit={aoSubmeterAjuste}>
          <h2>
            Ajustar saldo — lote #{loteAjuste.id} <span className="screen-tag">saldo atual: {loteAjuste.quantidade_atual}</span>
          </h2>
          <div className="grid">
            <div className="field">
              <label htmlFor="aj-novo-saldo">
                Novo saldo (contagem física) <span className="req">*</span>
              </label>
              <input
                id="aj-novo-saldo"
                type="number"
                min={0}
                value={novoSaldoAjuste}
                onChange={(e) => setNovoSaldoAjuste(e.target.value)}
                required
              />
              {diferencaAjuste != null && diferencaAjuste !== 0 && (
                <span className={diferencaAjuste > 0 ? 'ajuste-positivo' : 'ajuste-negativo'}>
                  diferença: {diferencaAjuste > 0 ? '+' : ''}
                  {diferencaAjuste}
                </span>
              )}
            </div>
            <div className="field">
              <label htmlFor="aj-motivo">
                Motivo <span className="req">*</span>
              </label>
              <input id="aj-motivo" type="text" value={motivoAjuste} onChange={(e) => setMotivoAjuste(e.target.value)} required />
            </div>
          </div>
          <div className="actions">
            <button
              type="submit"
              className="btn"
              disabled={salvandoAjuste || !motivoAjuste.trim() || diferencaAjuste === 0 || diferencaAjuste === null}
            >
              {salvandoAjuste ? 'Registrando…' : 'Confirmar ajuste'}
            </button>
            <button type="button" className="btn ghost" onClick={() => setLoteAjuste(null)}>
              Cancelar
            </button>
          </div>
        </form>
      )}

      <div className="panel">
        <div className="panel-head-busca">
          <h2>Catálogo</h2>
          <div style={{ display: 'flex', gap: 14, alignItems: 'center' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontWeight: 500, fontSize: 12.5 }}>
              <input type="checkbox" checked={mostrarInativos} onChange={(e) => setMostrarInativos(e.target.checked)} />
              Mostrar inativos
            </label>
            <input
              type="text"
              className="busca-estoque"
              placeholder="Buscar por código ou nome…"
              value={busca}
              onChange={(e) => setBusca(e.target.value)}
            />
          </div>
        </div>
        {carregando && <p className="carregando">Carregando…</p>}
        {!carregando && (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Código</th>
                  <th>Nome</th>
                  <th>Categoria</th>
                  <th className="num">Atual</th>
                  <th className="num">Mínimo</th>
                  <th></th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {itensFiltrados.length === 0 && (
                  <tr>
                    <td colSpan={7} className="vazio-tabela">
                      Nenhum item encontrado.
                    </td>
                  </tr>
                )}
                {itensFiltrados.map((item) => {
                  const critico = item.estoque_minimo > 0 && item.estoque_atual < item.estoque_minimo;
                  return (
                    <tr key={item.id}>
                      <td className="mono">{item.codigo}</td>
                      <td>
                        {item.nome}
                        {!item.ativo && <span className="pill muted" style={{ marginLeft: 8 }}>inativo</span>}
                      </td>
                      <td>{labelCategoriaItem(item.categoria)}</td>
                      <td className="num">{item.estoque_atual}</td>
                      <td className="num">{item.estoque_minimo}</td>
                      <td>{critico && <span className="pill danger">crítico</span>}</td>
                      <td style={{ display: 'flex', gap: 6, justifyContent: 'flex-end' }}>
                        {permissoes.gerenciarItens && (
                          <>
                            <button type="button" className="btn ghost sm" onClick={() => iniciarEdicaoItem(item)}>
                              Editar
                            </button>
                            <button
                              type="button"
                              className={`btn sm ${item.ativo ? 'danger' : 'ok'}`}
                              onClick={() => alternarAtivoItem(item)}
                            >
                              {item.ativo ? 'Desativar' : 'Reativar'}
                            </button>
                          </>
                        )}
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
        <h2>Lotes</h2>
        {carregando && <p className="carregando">Carregando…</p>}
        {!carregando && (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Item</th>
                  <th>Lote</th>
                  <th>Validade</th>
                  <th className="num">Qtd.</th>
                  <th className="num">Valor unit.</th>
                  <th>Origem</th>
                  <th></th>
                  {permissoes.ajustarEstoque && <th></th>}
                </tr>
              </thead>
              <tbody>
                {lotes.length === 0 && (
                  <tr>
                    <td colSpan={permissoes.ajustarEstoque ? 8 : 7} className="vazio-tabela">
                      Nenhum lote registrado.
                    </td>
                  </tr>
                )}
                {lotes.map((lote) => {
                  const nomeItem = lote.item?.nome ?? itens.find((i) => i.id === lote.item_id)?.nome ?? `#${lote.item_id}`;
                  const dias = lote.data_validade ? diasAteVencer(lote.data_validade) : null;
                  const nivel = dias !== null ? nivelValidade(dias) : null;
                  return (
                    <tr key={lote.id}>
                      <td>{nomeItem}</td>
                      <td className="mono">{lote.numero_lote ?? '—'}</td>
                      <td>{formatarData(lote.data_validade)}</td>
                      <td className="num">{lote.quantidade_atual}</td>
                      <td className="num">
                        {loteEditandoValorId === lote.id ? (
                          <div style={{ display: 'flex', gap: 4, alignItems: 'center', justifyContent: 'flex-end' }}>
                            <input
                              type="number"
                              min={0}
                              step="0.01"
                              className="qtd-input"
                              style={{ width: 90 }}
                              autoFocus
                              value={valorUnitarioEdit}
                              onChange={(e) => setValorUnitarioEdit(e.target.value)}
                            />
                            <button
                              type="button"
                              className="btn ghost sm"
                              disabled={salvandoValorUnitario}
                              onClick={() => salvarValorUnitario(lote.id)}
                            >
                              {salvandoValorUnitario ? '…' : 'Salvar'}
                            </button>
                            <button type="button" className="btn ghost sm" onClick={cancelarEdicaoValor}>
                              Cancelar
                            </button>
                          </div>
                        ) : (
                          <div style={{ display: 'flex', gap: 6, alignItems: 'center', justifyContent: 'flex-end' }}>
                            {formatarMoeda(lote.valor_unitario)}
                            {permissoes.gerenciarItens && (
                              <button type="button" className="btn ghost sm" onClick={() => abrirEdicaoValor(lote)}>
                                Editar
                              </button>
                            )}
                          </div>
                        )}
                      </td>
                      <td>{labelOrigemLote(lote.origem)}</td>
                      <td>
                        {nivel === 'vencido' && <span className="pill danger">venceu há {Math.abs(dias ?? 0)}d</span>}
                        {nivel === 'amarelo' && <span className="pill pend">vence em {dias}d</span>}
                        {nivel === 'roxo' && <span className="pill roxo">vence em {dias}d</span>}
                        {nivel === 'ok' && <span className="pill ok">ok</span>}
                        {nivel === null && <span className="pill muted">não vence</span>}
                      </td>
                      {permissoes.ajustarEstoque && (
                        <td>
                          <button type="button" className="btn ghost sm" onClick={() => abrirAjuste(lote)}>
                            Ajustar
                          </button>
                        </td>
                      )}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}
