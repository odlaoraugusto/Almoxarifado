import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { useAuth } from '../context/AuthContext';
import { api, mensagemErro } from '../lib/api';
import { permissoesDe } from '../lib/permissoes';
import { Alerta } from '../components/Alerta';
import { BuscaAutocomplete } from '../components/BuscaAutocomplete';
import { formatarData } from '../lib/formato';
import type { DescarteCriarPayload, LoteOut } from '../types';

type AbaSaida = 'vencimento';

/** Saída — hoje só a aba "Vencimento" (baixa de lote vencido, 2026-09-02,
 * pedido do cliente), com espaço pra outras modalidades de saída no
 * futuro. Sem campo de setor: diferente de Pedido (setor pede material)
 * e Empréstimo (unidade externa), aqui é só "isso venceu, dá baixa". */
export function SaidaPage() {
  const { usuario, matrizPermissoes } = useAuth();
  const permissoes = permissoesDe(usuario, matrizPermissoes);

  const [aba] = useState<AbaSaida>('vencimento');

  if (!permissoes.descarteVencimento) {
    return (
      <section>
        <div className="screen-head">
          <h1>Saída</h1>
        </div>
        <div className="locked-panel">
          <span className="lock-icon">🔒</span>
          Seu perfil não tem permissão para registrar saída.
        </div>
      </section>
    );
  }

  return (
    <section>
      <div className="screen-head">
        <h1>Saída</h1>
      </div>

      <div className="tabs2" role="tablist">
        <button type="button" role="tab" className="tab2" aria-selected={aba === 'vencimento'}>
          Vencimento
        </button>
      </div>

      {aba === 'vencimento' && <FormularioBaixaVencimento />}
    </section>
  );
}

function FormularioBaixaVencimento() {
  const { token } = useAuth();

  const [lotes, setLotes] = useState<LoteOut[]>([]);
  const [carregandoLotes, setCarregandoLotes] = useState(true);
  const [erroCarga, setErroCarga] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    setCarregandoLotes(true);
    api
      .get<LoteOut[]>('/lotes', { token })
      .then(setLotes)
      .catch((err) => setErroCarga(mensagemErro(err, 'Não foi possível carregar os lotes.')))
      .finally(() => setCarregandoLotes(false));
  }, [token]);

  const lotesComSaldo = lotes.filter((l) => l.quantidade_atual > 0);

  const [buscaLote, setBuscaLote] = useState('');
  const [loteSelecionado, setLoteSelecionado] = useState<LoteOut | null>(null);
  const [quantidade, setQuantidade] = useState('');
  const [motivo, setMotivo] = useState('Vencido');

  const [erroValidacao, setErroValidacao] = useState<string | null>(null);
  const [erroEnvio, setErroEnvio] = useState<string | null>(null);
  const [sucesso, setSucesso] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  function rotuloLote(lote: LoteOut): string {
    const nomeItem = lote.item?.nome ?? `item #${lote.item_id}`;
    const validade = formatarData(lote.data_validade);
    return `${nomeItem} — lote ${lote.numero_lote ?? '—'} — vence ${validade} — saldo ${lote.quantidade_atual}`;
  }

  function selecionarLote(lote: LoteOut) {
    setLoteSelecionado(lote);
    setBuscaLote(rotuloLote(lote));
    setQuantidade(String(lote.quantidade_atual));
    setSucesso(null);
    setErroValidacao(null);
  }

  function limparFormulario() {
    setLoteSelecionado(null);
    setBuscaLote('');
    setQuantidade('');
    setMotivo('Vencido');
  }

  async function aoSubmeter(e: FormEvent) {
    e.preventDefault();
    setErroValidacao(null);
    setErroEnvio(null);
    setSucesso(null);

    if (!loteSelecionado) {
      setErroValidacao('Selecione o lote vencido.');
      return;
    }
    const qtd = Number(quantidade);
    if (!qtd || qtd <= 0) {
      setErroValidacao('Informe uma quantidade válida.');
      return;
    }
    if (qtd > loteSelecionado.quantidade_atual) {
      setErroValidacao(`Quantidade maior que o saldo do lote (saldo: ${loteSelecionado.quantidade_atual}).`);
      return;
    }
    if (!motivo.trim()) {
      setErroValidacao('Informe o motivo da baixa.');
      return;
    }

    const payload: DescarteCriarPayload = {
      lote_id: loteSelecionado.id,
      quantidade: qtd,
      motivo_descarte: motivo.trim(),
    };

    setEnviando(true);
    try {
      await api.post('/descartes', payload, { token });
      setSucesso('Baixa por vencimento registrada.');
      limparFormulario();
      // Reflete o novo saldo na lista local, sem precisar recarregar tudo.
      setLotes((atual) =>
        atual.map((l) => (l.id === payload.lote_id ? { ...l, quantidade_atual: l.quantidade_atual - qtd } : l)),
      );
    } catch (err) {
      setErroEnvio(mensagemErro(err, 'Não foi possível registrar a baixa.'));
    } finally {
      setEnviando(false);
    }
  }

  return (
    <form className="panel" onSubmit={aoSubmeter}>
      <h2>Baixa por vencimento</h2>
      <p className="screen-sub" style={{ marginTop: -4 }}>
        Escolha o lote vencido e a quantidade — sem setor, é só a baixa do que não pode mais ser usado.
      </p>

      {erroCarga && <Alerta tipo="erro">{erroCarga}</Alerta>}
      {erroValidacao && <Alerta tipo="erro">{erroValidacao}</Alerta>}
      {erroEnvio && <Alerta tipo="erro">{erroEnvio}</Alerta>}
      {sucesso && <Alerta tipo="sucesso">{sucesso}</Alerta>}

      <div className="grid">
        <div className="field span2">
          <label htmlFor="busca-lote-descarte">
            Lote vencido <span className="req">*</span>
          </label>
          <BuscaAutocomplete
            id="busca-lote-descarte"
            itens={lotesComSaldo}
            valor={buscaLote}
            aoMudarValor={(v) => {
              setBuscaLote(v);
              setLoteSelecionado(null);
            }}
            rotulo={rotuloLote}
            chave={(l) => l.id}
            aoSelecionar={selecionarLote}
            placeholder={carregandoLotes ? 'Carregando lotes…' : 'buscar por item ou nº do lote…'}
            disabled={carregandoLotes}
          />
        </div>
        <div className="field">
          <label htmlFor="qtd-descarte">
            Quantidade <span className="req">*</span>
          </label>
          <input
            id="qtd-descarte"
            type="number"
            min={1}
            max={loteSelecionado?.quantidade_atual}
            value={quantidade}
            onChange={(e) => setQuantidade(e.target.value)}
            disabled={!loteSelecionado}
          />
        </div>
        <div className="field">
          <label htmlFor="motivo-descarte">
            Motivo <span className="req">*</span>
          </label>
          <input
            id="motivo-descarte"
            type="text"
            value={motivo}
            onChange={(e) => setMotivo(e.target.value)}
            disabled={!loteSelecionado}
          />
        </div>
      </div>

      <div className="actions">
        <button type="submit" className="btn" disabled={enviando || !loteSelecionado}>
          {enviando ? 'Registrando…' : 'Confirmar baixa'}
        </button>
      </div>
    </form>
  );
}
