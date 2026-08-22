import { useMemo, useState } from 'react';
import { BuscaAutocomplete } from './BuscaAutocomplete';
import type { ItemOut } from '../types';

export interface LinhaItemEntrada {
  item: ItemOut;
  quantidade: string;
  numeroLote: string;
  dataValidade: string;
  valorUnitario: string;
}

export function linhaVazia(item: ItemOut): LinhaItemEntrada {
  return { item, quantidade: '1', numeroLote: '', dataValidade: '', valorUnitario: '' };
}

interface SeletorItensEntradaProps {
  idBusca?: string;
  itensDisponiveis: ItemOut[];
  carregandoItens?: boolean;
  linhas: LinhaItemEntrada[];
  aoMudarLinhas: (linhas: LinhaItemEntrada[]) => void;
  /** Nº do lote / validade / valor unitário só fazem sentido quando a
   * linha vai gerar um lote novo (Entrada por Compra, ou Empréstimo na
   * direção "entrada") — escondidos quando não (Empréstimo "saída"). */
  mostrarCamposLote?: boolean;
}

/** Busca+adicionar item de catálogo numa tabela editável — mesma UX do
 * formulário público de pedido (`PedidoPublicoPage`), generalizada para
 * as telas autenticadas que registram lote(s) novos (Entrada por Compra,
 * Empréstimos/Permutas). Cada linha adicionada tem quantidade sempre
 * editável e, opcionalmente, nº do lote/validade/valor unitário. */
export function SeletorItensEntrada({
  idBusca = 'seletor-busca-item',
  itensDisponiveis,
  carregandoItens,
  linhas,
  aoMudarLinhas,
  mostrarCamposLote = true,
}: SeletorItensEntradaProps) {
  const [busca, setBusca] = useState('');
  const [itemSelecionado, setItemSelecionado] = useState<ItemOut | null>(null);

  const itensParaBusca = useMemo(
    () => itensDisponiveis.filter((i) => !linhas.some((l) => l.item.id === i.id)),
    [itensDisponiveis, linhas],
  );

  function adicionar() {
    if (!itemSelecionado) return;
    aoMudarLinhas([...linhas, linhaVazia(itemSelecionado)]);
    setBusca('');
    setItemSelecionado(null);
  }

  function remover(itemId: number) {
    aoMudarLinhas(linhas.filter((l) => l.item.id !== itemId));
  }

  function atualizar(itemId: number, patch: Partial<LinhaItemEntrada>) {
    aoMudarLinhas(linhas.map((l) => (l.item.id === itemId ? { ...l, ...patch } : l)));
  }

  const colunas = mostrarCamposLote ? 6 : 3;

  return (
    <div>
      <div className="field">
        <label htmlFor={idBusca}>Buscar item do catálogo</label>
        <div style={{ display: 'flex', gap: 8 }}>
          <div style={{ flex: 1 }}>
            <BuscaAutocomplete
              id={idBusca}
              itens={itensParaBusca}
              valor={busca}
              aoMudarValor={(v) => {
                setBusca(v);
                setItemSelecionado(null);
              }}
              rotulo={(item) => `${item.codigo} — ${item.nome}`}
              chave={(item) => item.id}
              aoSelecionar={(item) => {
                setItemSelecionado(item);
                setBusca(`${item.codigo} — ${item.nome}`);
              }}
              placeholder={carregandoItens ? 'Carregando catálogo…' : 'Código ou nome do item…'}
              disabled={carregandoItens}
            />
          </div>
          <button type="button" className="btn ghost" disabled={!itemSelecionado} onClick={adicionar}>
            + Adicionar
          </button>
        </div>
      </div>

      <div className="table-wrap" style={{ marginTop: 14 }}>
        <table>
          <thead>
            <tr>
              <th>Item</th>
              {mostrarCamposLote && <th>Nº do lote</th>}
              {mostrarCamposLote && <th>Validade</th>}
              <th className="num">Quantidade</th>
              {mostrarCamposLote && <th className="num">Valor unit.</th>}
              <th></th>
            </tr>
          </thead>
          <tbody>
            {linhas.length === 0 && (
              <tr>
                <td colSpan={colunas} className="vazio-tabela">
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
                  {l.item.apresentacao && (
                    <div style={{ fontSize: 11, color: 'var(--muted)' }}>{l.item.apresentacao}</div>
                  )}
                </td>
                {mostrarCamposLote && (
                  <td>
                    <input
                      type="text"
                      value={l.numeroLote}
                      onChange={(e) => atualizar(l.item.id, { numeroLote: e.target.value })}
                    />
                  </td>
                )}
                {mostrarCamposLote && (
                  <td>
                    <input
                      type="date"
                      value={l.dataValidade}
                      onChange={(e) => atualizar(l.item.id, { dataValidade: e.target.value })}
                    />
                  </td>
                )}
                <td className="num">
                  <input
                    type="number"
                    min={1}
                    style={{ width: 90 }}
                    value={l.quantidade}
                    onChange={(e) => atualizar(l.item.id, { quantidade: e.target.value })}
                    required
                  />
                </td>
                {mostrarCamposLote && (
                  <td className="num">
                    <input
                      type="text"
                      placeholder="0,00"
                      style={{ width: 100 }}
                      value={l.valorUnitario}
                      onChange={(e) => atualizar(l.item.id, { valorUnitario: e.target.value })}
                    />
                  </td>
                )}
                <td>
                  <button type="button" className="btn ghost sm" onClick={() => remover(l.item.id)}>
                    Remover
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
