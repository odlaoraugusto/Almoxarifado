import { useEffect, useMemo, useRef, useState } from 'react';
import type { FormEvent, KeyboardEvent } from 'react';
import { jsPDF } from 'jspdf';
import { api, mensagemErro } from '../lib/api';
import { HOSPITAL_SIGLA } from '../lib/instituicao';
import type { ItemPublico, PedidoCriarPayload, PedidoOut, Setor } from '../types';

interface LinhaPedido {
  item: ItemPublico;
  quantidade: number;
}

function normalizar(texto: string): string {
  return texto
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '')
    .toLowerCase();
}

/** Formulário público de pedido de material — sem login, acessível a
 * qualquer pessoa da organização. Adaptado quase literalmente do
 * protótipo aprovado pelo cliente (docs/prototipo_formulario_publico.html):
 * mesma UX de busca/adicionar item, tabela de itens do pedido e modal de
 * sucesso com comprovante em PDF — só a fonte de dados mudou (Apps
 * Script/Sheets -> nossa API). */
export function PedidoPublicoPage() {
  const [setores, setSetores] = useState<Setor[]>([]);
  const [catalogo, setCatalogo] = useState<ItemPublico[]>([]);
  const [erroCarga, setErroCarga] = useState<string | null>(null);
  const [carregandoCatalogo, setCarregandoCatalogo] = useState(true);

  useEffect(() => {
    let cancelado = false;
    Promise.all([api.get<Setor[]>('/setores/publico'), api.get<ItemPublico[]>('/itens/publico')])
      .then(([setoresResp, itensResp]) => {
        if (cancelado) return;
        setSetores(setoresResp);
        setCatalogo(itensResp);
      })
      .catch((err) => {
        if (cancelado) return;
        setErroCarga(mensagemErro(err, 'Não foi possível carregar o estoque/setores. Recarregue a página.'));
      })
      .finally(() => {
        if (!cancelado) setCarregandoCatalogo(false);
      });
    return () => {
      cancelado = true;
    };
  }, []);

  const [setorId, setSetorId] = useState('');
  const [responsavel, setResponsavel] = useState('');
  const [observacao, setObservacao] = useState('');

  const [busca, setBusca] = useState('');
  const [itemSelecionado, setItemSelecionado] = useState<ItemPublico | null>(null);
  const [sugestoesAbertas, setSugestoesAbertas] = useState(false);
  const [indiceAtivo, setIndiceAtivo] = useState(-1);
  const buscaWrapperRef = useRef<HTMLDivElement>(null);

  const [linhas, setLinhas] = useState<LinhaPedido[]>([]);

  const [errosValidacao, setErrosValidacao] = useState<string[]>([]);
  const [enviando, setEnviando] = useState(false);
  const [erroEnvio, setErroEnvio] = useState<string | null>(null);
  const [resultado, setResultado] = useState<PedidoOut | null>(null);

  useEffect(() => {
    function aoClicarFora(e: MouseEvent) {
      if (buscaWrapperRef.current && !buscaWrapperRef.current.contains(e.target as Node)) {
        setSugestoesAbertas(false);
      }
    }
    document.addEventListener('click', aoClicarFora);
    return () => document.removeEventListener('click', aoClicarFora);
  }, []);

  const sugestoes = useMemo(() => {
    const termo = normalizar(busca.trim());
    if (!termo) return [];
    return catalogo
      .filter((item) => normalizar(item.codigo).includes(termo) || normalizar(item.nome).includes(termo))
      .slice(0, 8);
  }, [busca, catalogo]);

  function aoDigitarBusca(valor: string) {
    setBusca(valor);
    setItemSelecionado(null);
    setSugestoesAbertas(true);
    setIndiceAtivo(-1);
  }

  function escolherSugestao(item: ItemPublico) {
    setItemSelecionado(item);
    setBusca(`${item.codigo} - ${item.nome}`);
    setSugestoesAbertas(false);
    setIndiceAtivo(-1);
  }

  function adicionarItemSelecionado() {
    if (!itemSelecionado) return;
    setLinhas((atual) => {
      if (atual.some((l) => l.item.id === itemSelecionado.id)) return atual;
      return [...atual, { item: itemSelecionado, quantidade: 1 }];
    });
    setBusca('');
    setItemSelecionado(null);
  }

  function aoTeclarBusca(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'ArrowDown' && sugestoes.length) {
      e.preventDefault();
      setIndiceAtivo((i) => (i + 1) % sugestoes.length);
    } else if (e.key === 'ArrowUp' && sugestoes.length) {
      e.preventDefault();
      setIndiceAtivo((i) => (i - 1 + sugestoes.length) % sugestoes.length);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (indiceAtivo >= 0 && sugestoes[indiceAtivo]) {
        escolherSugestao(sugestoes[indiceAtivo]);
      } else if (itemSelecionado) {
        adicionarItemSelecionado();
      } else if (sugestoes.length === 1) {
        escolherSugestao(sugestoes[0]);
      }
    } else if (e.key === 'Escape') {
      setSugestoesAbertas(false);
    }
  }

  function atualizarQuantidade(itemId: number, valor: string) {
    const qtd = parseInt(valor, 10);
    setLinhas((atual) => atual.map((l) => (l.item.id === itemId ? { ...l, quantidade: qtd > 0 ? qtd : 1 } : l)));
  }

  function removerItem(itemId: number) {
    setLinhas((atual) => atual.filter((l) => l.item.id !== itemId));
  }

  function validar(): string[] {
    const erros: string[] = [];
    if (!setorId) erros.push('Setor Solicitante');
    if (!responsavel.trim()) erros.push('Responsável pelo Pedido');
    if (linhas.length === 0) erros.push('É necessário adicionar ao menos um item do almoxarifado');
    return erros;
  }

  async function aoSubmeter(e: FormEvent) {
    e.preventDefault();
    const erros = validar();
    setErrosValidacao(erros);
    if (erros.length > 0) {
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }

    setErroEnvio(null);
    setEnviando(true);
    const payload: PedidoCriarPayload = {
      setor_id: Number(setorId),
      responsavel_solicitante: responsavel.trim(),
      observacao: observacao.trim() || undefined,
      itens: linhas.map((l) => ({ item_id: l.item.id, quantidade_solicitada: l.quantidade })),
    };

    try {
      const resposta = await api.post<PedidoOut>('/pedidos', payload);
      setResultado(resposta);
    } catch (err) {
      setErroEnvio(mensagemErro(err, 'Não foi possível registrar o pedido. Nenhum item foi descontado do estoque.'));
    } finally {
      setEnviando(false);
    }
  }

  function novoPedido() {
    setResultado(null);
    setSetorId('');
    setResponsavel('');
    setObservacao('');
    setLinhas([]);
    setBusca('');
    setErrosValidacao([]);
  }

  function baixarComprovante() {
    if (!resultado) return;
    const setorNome = setores.find((s) => s.id === resultado.setor_id)?.nome ?? '—';
    const roxo: [number, number, number] = [97, 53, 140];

    const doc = new jsPDF();
    doc.setFontSize(14);
    doc.setTextColor(...roxo);
    doc.text(`Comprovante de Pedido — Almoxarifado ${HOSPITAL_SIGLA}`, 14, 18);
    doc.setDrawColor(...roxo);
    doc.line(14, 22, 196, 22);

    doc.setFontSize(11);
    doc.setTextColor(60, 60, 60);
    let y = 32;
    const linha = (label: string, valor: string) => {
      doc.setFont('helvetica', 'bold');
      doc.text(label, 14, y);
      doc.setFont('helvetica', 'normal');
      doc.text(valor || '-', 55, y);
      y += 8;
    };

    linha('Protocolo:', `#${resultado.id}`);
    linha('Data/Hora:', new Date(resultado.data_hora).toLocaleString('pt-BR'));
    linha('Setor:', setorNome);
    linha('Responsável:', resultado.responsavel_solicitante);
    if (resultado.observacao) linha('Observação:', resultado.observacao);

    y += 4;
    doc.setFont('helvetica', 'bold');
    doc.text('Itens Solicitados', 14, y);
    y += 6;
    doc.setFont('helvetica', 'normal');
    for (const linhaItem of linhas) {
      doc.text(`• ${linhaItem.item.codigo} - ${linhaItem.item.nome} — Qtd: ${linhaItem.quantidade}`, 16, y);
      y += 7;
    }

    doc.setFontSize(9);
    doc.setTextColor(140, 140, 140);
    doc.text('Documento gerado automaticamente pelo sistema de solicitação de materiais.', 14, 285);
    doc.save(`comprovante_pedido_${resultado.id}.pdf`);
  }

  return (
    <div className="pedido-publico">
      {errosValidacao.length > 0 && (
        <div className="validation-alert">
          <h4>Falta preencher os seguintes campos obrigatórios:</h4>
          <ul>
            {errosValidacao.map((erro) => (
              <li key={erro}>{erro}</li>
            ))}
          </ul>
        </div>
      )}

      {erroCarga && <div className="conexao-alert">⚠️ {erroCarga}</div>}
      {erroEnvio && <div className="conexao-alert">⚠️ {erroEnvio}</div>}

      <div className="container">
        <header>
          <h1>Solicitação de Materiais — Almoxarifado</h1>
          <div className="subtitle">{HOSPITAL_SIGLA}</div>
        </header>

        <form onSubmit={aoSubmeter}>
          <section>
            <div className="section-title">Identificação do Setor</div>
            <div className="grid-pub grid-pub-2">
              <div className="form-group">
                <label htmlFor="pp-setor">Setor Solicitante *</label>
                <select id="pp-setor" value={setorId} onChange={(e) => setSetorId(e.target.value)} required>
                  <option value="">{carregandoCatalogo ? 'Carregando setores...' : 'Selecione o setor...'}</option>
                  {setores.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.nome}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label htmlFor="pp-responsavel">Responsável pelo Pedido *</label>
                <input
                  id="pp-responsavel"
                  type="text"
                  placeholder="Nome do colaborador"
                  value={responsavel}
                  onChange={(e) => setResponsavel(e.target.value)}
                  required
                />
              </div>
            </div>
          </section>

          <section>
            <div className="section-title">Itens Requisitados</div>

            <div className="form-group">
              <label htmlFor="pp-busca">Buscar Material no Estoque</label>
              <div className="busca-item-wrapper" ref={buscaWrapperRef}>
                <div className="busca-item-linha">
                  <input
                    id="pp-busca"
                    type="text"
                    placeholder="Digite o código ou nome do material..."
                    autoComplete="off"
                    value={busca}
                    onChange={(e) => aoDigitarBusca(e.target.value)}
                    onFocus={() => busca.trim() && setSugestoesAbertas(true)}
                    onKeyDown={aoTeclarBusca}
                  />
                  <button type="button" className="btn-adicionar" disabled={!itemSelecionado} onClick={adicionarItemSelecionado}>
                    + Adicionar
                  </button>
                </div>
                {sugestoesAbertas && busca.trim() && (
                  <ul className="lista-sugestoes">
                    {sugestoes.length === 0 && <li className="sem-resultado">Nenhum material encontrado</li>}
                    {sugestoes.map((item, idx) => {
                      const jaAdicionado = linhas.some((l) => l.item.id === item.id);
                      return (
                        <li
                          key={item.id}
                          className={`${jaAdicionado ? 'ja-adicionado' : ''} ${idx === indiceAtivo ? 'ativa' : ''}`.trim()}
                          onClick={() => !jaAdicionado && escolherSugestao(item)}
                        >
                          <span className="nome-item">
                            <span>{item.codigo}</span> — {item.nome}
                            {jaAdicionado ? ' (já adicionado)' : ''}
                          </span>
                          <span className="badge-categoria">{item.categoria ?? '—'}</span>
                        </li>
                      );
                    })}
                  </ul>
                )}
              </div>
              <div className={`estoque-status ${erroCarga ? 'erro' : ''}`}>
                {erroCarga
                  ? 'Falha ao carregar o estoque.'
                  : carregandoCatalogo
                    ? 'Carregando estoque...'
                    : `${catalogo.length} itens disponíveis no estoque.`}
              </div>
            </div>

            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th style={{ width: '50%' }}>Item Selecionado</th>
                    <th style={{ width: '22%' }}>Categoria</th>
                    <th style={{ width: '18%' }}>Quantidade *</th>
                    <th style={{ width: '10%' }}></th>
                  </tr>
                </thead>
                <tbody>
                  {linhas.length === 0 && (
                    <tr>
                      <td colSpan={4} style={{ textAlign: 'center', color: 'var(--muted)', fontStyle: 'italic' }}>
                        Nenhum item adicionado ainda.
                      </td>
                    </tr>
                  )}
                  {linhas.map((l) => (
                    <tr key={l.item.id}>
                      <td>
                        <b>
                          {l.item.codigo} - {l.item.nome}
                        </b>
                        <br />
                        <span style={{ fontSize: 11, color: 'var(--muted)' }}>{l.item.apresentacao ?? ''}</span>
                      </td>
                      <td>
                        <span className="badge-categoria">{l.item.categoria ?? '—'}</span>
                      </td>
                      <td>
                        <input
                          type="number"
                          className="qtd-input"
                          min={1}
                          value={l.quantidade}
                          onChange={(e) => atualizarQuantidade(l.item.id, e.target.value)}
                          required
                        />
                      </td>
                      <td>
                        <button type="button" className="btn-remover" title="Remover item" onClick={() => removerItem(l.item.id)}>
                          ✕
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="form-group" style={{ marginTop: 12 }}>
              <label htmlFor="pp-observacao">Observação (opcional)</label>
              <textarea
                id="pp-observacao"
                placeholder="Ex: uso emergencial, cobertura de plantão, etc."
                value={observacao}
                onChange={(e) => setObservacao(e.target.value)}
              />
            </div>
          </section>

          <button type="submit" className="btn-acao" disabled={enviando || carregandoCatalogo || !!erroCarga}>
            {enviando ? 'Enviando…' : 'Confirmar Pedido de Material'}
          </button>
        </form>
      </div>

      {(enviando || resultado) && (
        <div className="pp-modal-overlay">
          <div className="pp-modal-content">
            {enviando && (
              <div>
                <div className="pp-spinner" />
                <div className="pp-modal-header" style={{ border: 'none' }}>
                  Processando Pedido...
                </div>
                <div className="pp-modal-body">Registrando sua solicitação.</div>
              </div>
            )}
            {!enviando && resultado && (
              <div>
                <div className="pp-modal-header" style={{ color: 'var(--fesf-mint)' }}>
                  Pedido Registrado!
                </div>
                <div className="pp-modal-body">
                  O seu pedido foi gerado com sucesso sob o protocolo:
                  <span className="protocolo-numero">#{resultado.id}</span>
                  Guarde este número — ele não exige login para consultar depois.
                </div>
                <button type="button" className="pp-btn-modal" onClick={baixarComprovante}>
                  Baixar Comprovante em PDF
                </button>
                <button type="button" className="pp-btn-modal secundario" onClick={novoPedido}>
                  Fechar e Novo Pedido
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
