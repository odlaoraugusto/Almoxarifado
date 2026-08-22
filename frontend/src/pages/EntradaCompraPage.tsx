import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { useAuth } from '../context/AuthContext';
import { api, mensagemErro } from '../lib/api';
import { Alerta } from '../components/Alerta';
import { SeletorItensEntrada } from '../components/SeletorItensEntrada';
import type { LinhaItemEntrada } from '../components/SeletorItensEntrada';
import type { EntradaCriarPayload, ItemOut } from '../types';

/** Entrada por Compra — uma compra = um nº de nota fiscal (+ AFM
 * opcional) com vários itens, cada um virando um lote próprio. Não
 * existe endpoint de "criar vários lotes de uma vez": chama
 * `POST /itens/{item_id}/entrada` uma vez por linha adicionada,
 * sequencialmente, repetindo o cabeçalho (nota fiscal/AFM) em cada
 * chamada — mesmo padrão de confirmação sequencial já usado no Painel
 * (conferência de pedido). Liberado a qualquer perfil autenticado. */
export function EntradaCompraPage() {
  const { token } = useAuth();

  const [itens, setItens] = useState<ItemOut[]>([]);
  const [carregandoItens, setCarregandoItens] = useState(true);
  const [erroCarga, setErroCarga] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    setCarregandoItens(true);
    api
      .get<ItemOut[]>('/itens', { token })
      .then(setItens)
      .catch((err) => setErroCarga(mensagemErro(err, 'Não foi possível carregar o catálogo.')))
      .finally(() => setCarregandoItens(false));
  }, [token]);

  const [numeroNotaFiscal, setNumeroNotaFiscal] = useState('');
  const [numeroAfm, setNumeroAfm] = useState('');
  const [linhas, setLinhas] = useState<LinhaItemEntrada[]>([]);

  const [erroValidacao, setErroValidacao] = useState<string | null>(null);
  const [erroEnvio, setErroEnvio] = useState<string | null>(null);
  const [sucesso, setSucesso] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  function limparFormulario() {
    setNumeroNotaFiscal('');
    setNumeroAfm('');
    setLinhas([]);
  }

  async function aoSubmeter(e: FormEvent) {
    e.preventDefault();
    setErroValidacao(null);
    setErroEnvio(null);
    setSucesso(null);

    if (!numeroNotaFiscal.trim()) {
      setErroValidacao('Informe o número da nota fiscal.');
      return;
    }
    if (linhas.length === 0) {
      setErroValidacao('Adicione ao menos um item da compra.');
      return;
    }
    for (const l of linhas) {
      const qtd = Number(l.quantidade);
      if (!qtd || qtd <= 0) {
        setErroValidacao(`Informe uma quantidade válida para "${l.item.nome}".`);
        return;
      }
    }

    setEnviando(true);
    let registrados = 0;
    try {
      for (const l of linhas) {
        const payload: EntradaCriarPayload = {
          numero_lote: l.numeroLote.trim() || undefined,
          data_validade: l.dataValidade || undefined,
          quantidade: Number(l.quantidade),
          valor_unitario: l.valorUnitario.trim() || undefined,
          origem: 'compra',
          numero_nota_fiscal: numeroNotaFiscal.trim(),
          numero_afm: numeroAfm.trim() || undefined,
        };
        // eslint-disable-next-line no-await-in-loop -- uma chamada por linha, de propósito (não existe endpoint em lote)
        await api.post(`/itens/${l.item.id}/entrada`, payload, { token });
        registrados++;
      }
      setSucesso(`Entrada registrada — ${registrados} ${registrados === 1 ? 'lote criado' : 'lotes criados'} para a NF ${numeroNotaFiscal.trim()}.`);
      limparFormulario();
    } catch (err) {
      setErroEnvio(
        mensagemErro(
          err,
          `Não foi possível registrar a entrada. ${registrados} ${registrados === 1 ? 'item já havia sido' : 'itens já haviam sido'} registrado(s) antes do erro — confira no Estoque antes de repetir.`,
        ),
      );
      setLinhas((atual) => atual.slice(registrados));
    } finally {
      setEnviando(false);
    }
  }

  return (
    <section>
      <div className="screen-head">
        <h1>Entrada por Compra</h1>
        <span className="screen-tag">nota fiscal + itens</span>
      </div>
      <p className="screen-sub">
        Uma compra = uma nota fiscal (com AFM opcional) e vários itens — cada item vira um lote próprio no estoque.
      </p>

      {erroCarga && <Alerta tipo="erro">{erroCarga}</Alerta>}
      {erroValidacao && <Alerta tipo="erro">{erroValidacao}</Alerta>}
      {erroEnvio && <Alerta tipo="erro">{erroEnvio}</Alerta>}
      {sucesso && <Alerta tipo="sucesso">{sucesso}</Alerta>}

      <form className="panel" onSubmit={aoSubmeter}>
        <h2>Dados da compra</h2>
        <div className="grid">
          <div className="field">
            <label htmlFor="ec-nf">
              Nº nota fiscal <span className="req">*</span>
            </label>
            <input
              id="ec-nf"
              type="text"
              value={numeroNotaFiscal}
              onChange={(e) => setNumeroNotaFiscal(e.target.value)}
              required
            />
          </div>
          <div className="field">
            <label htmlFor="ec-afm">
              Nº AFM <span className="tag">opcional</span>
            </label>
            <input id="ec-afm" type="text" value={numeroAfm} onChange={(e) => setNumeroAfm(e.target.value)} />
          </div>
        </div>

        <h2 style={{ marginTop: 22 }}>Itens da compra</h2>
        <SeletorItensEntrada
          idBusca="ec-busca-item"
          itensDisponiveis={itens}
          carregandoItens={carregandoItens}
          linhas={linhas}
          aoMudarLinhas={setLinhas}
        />

        <div className="actions">
          <button type="submit" className="btn" disabled={enviando}>
            {enviando ? 'Registrando…' : 'Registrar entrada'}
          </button>
        </div>
      </form>
    </section>
  );
}
