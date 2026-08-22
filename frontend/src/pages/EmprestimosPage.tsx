import { useCallback, useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { useAuth } from '../context/AuthContext';
import { api, mensagemErro } from '../lib/api';
import { Alerta } from '../components/Alerta';
import { SeletorItensEntrada } from '../components/SeletorItensEntrada';
import type { LinhaItemEntrada } from '../components/SeletorItensEntrada';
import { formatarDataHora } from '../lib/formato';
import type { DirecaoEmprestimo, EmprestimoCriarPayload, EmprestimoOut, ItemOut } from '../types';

const DIRECAO_LABEL: Record<DirecaoEmprestimo, string> = {
  saida: 'Saída (emprestar pra fora)',
  entrada: 'Entrada (devolução / permuta recebida)',
};

/** Empréstimo/permuta de material com unidade externa (fora do nosso
 * catálogo de setores). "Saída" consome estoque nosso; "Entrada"
 * (devolução ou permuta) cria lote(s) novo(s), igual à Entrada por
 * Compra — só que aqui o backend aceita a lista inteira de itens numa
 * única chamada (`POST /emprestimos`), diferente da Entrada por Compra.
 * Liberado a qualquer perfil autenticado. */
export function EmprestimosPage() {
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

  const [direcao, setDirecao] = useState<DirecaoEmprestimo>('saida');
  const [unidadeOrigem, setUnidadeOrigem] = useState('');
  const [numeroOficio, setNumeroOficio] = useState('');
  const [linhas, setLinhas] = useState<LinhaItemEntrada[]>([]);

  const [erroValidacao, setErroValidacao] = useState<string | null>(null);
  const [erroEnvio, setErroEnvio] = useState<string | null>(null);
  const [sucesso, setSucesso] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  function mudarDirecao(nova: DirecaoEmprestimo) {
    setDirecao(nova);
    // Lote/validade/valor só existem no formulário quando a direção é
    // "entrada" — limpa esses campos ao trocar pra "saída" pra não
    // mandar lixo escondido no payload.
    if (nova === 'saida') {
      setLinhas((atual) => atual.map((l) => ({ ...l, numeroLote: '', dataValidade: '', valorUnitario: '' })));
    }
  }

  function limparFormulario() {
    setUnidadeOrigem('');
    setNumeroOficio('');
    setLinhas([]);
  }

  // ---- histórico ----
  const [historico, setHistorico] = useState<EmprestimoOut[]>([]);
  const [carregandoHistorico, setCarregandoHistorico] = useState(true);
  const [erroHistorico, setErroHistorico] = useState<string | null>(null);

  const carregarHistorico = useCallback(() => {
    if (!token) return;
    setCarregandoHistorico(true);
    setErroHistorico(null);
    api
      .get<EmprestimoOut[]>('/emprestimos', { token })
      .then(setHistorico)
      .catch((err) => setErroHistorico(mensagemErro(err, 'Não foi possível carregar o histórico.')))
      .finally(() => setCarregandoHistorico(false));
  }, [token]);

  useEffect(() => {
    carregarHistorico();
  }, [carregarHistorico]);

  async function aoSubmeter(e: FormEvent) {
    e.preventDefault();
    setErroValidacao(null);
    setErroEnvio(null);
    setSucesso(null);

    if (!unidadeOrigem.trim()) {
      setErroValidacao('Informe a unidade de origem (instituição externa).');
      return;
    }
    if (linhas.length === 0) {
      setErroValidacao('Adicione ao menos um item.');
      return;
    }
    for (const l of linhas) {
      const qtd = Number(l.quantidade);
      if (!qtd || qtd <= 0) {
        setErroValidacao(`Informe uma quantidade válida para "${l.item.nome}".`);
        return;
      }
    }

    const payload: EmprestimoCriarPayload = {
      direcao,
      unidade_origem: unidadeOrigem.trim(),
      numero_oficio: numeroOficio.trim() || undefined,
      itens: linhas.map((l) => ({
        item_id: l.item.id,
        quantidade: Number(l.quantidade),
        numero_lote: direcao === 'entrada' ? l.numeroLote.trim() || undefined : undefined,
        data_validade: direcao === 'entrada' ? l.dataValidade || undefined : undefined,
        valor_unitario: direcao === 'entrada' ? l.valorUnitario.trim() || undefined : undefined,
      })),
    };

    setEnviando(true);
    try {
      await api.post('/emprestimos', payload, { token });
      setSucesso(direcao === 'saida' ? 'Saída de empréstimo registrada.' : 'Entrada registrada.');
      limparFormulario();
      carregarHistorico();
    } catch (err) {
      setErroEnvio(mensagemErro(err, 'Não foi possível registrar o empréstimo/permuta.'));
    } finally {
      setEnviando(false);
    }
  }

  function itensResumo(emp: EmprestimoOut): string {
    return emp.itens.map((it) => `${it.item.nome} × ${it.quantidade}`).join('; ');
  }

  return (
    <section>
      <div className="screen-head">
        <h1>Empréstimos e Permutas</h1>
        <span className="screen-tag">unidades externas</span>
      </div>
      <p className="screen-sub">
        Registro de empréstimo ou permuta de material com uma unidade externa ao almoxarifado (outra instituição —
        fora do nosso catálogo de setores).
      </p>

      {erroCarga && <Alerta tipo="erro">{erroCarga}</Alerta>}
      {erroValidacao && <Alerta tipo="erro">{erroValidacao}</Alerta>}
      {erroEnvio && <Alerta tipo="erro">{erroEnvio}</Alerta>}
      {sucesso && <Alerta tipo="sucesso">{sucesso}</Alerta>}

      <form className="panel" onSubmit={aoSubmeter}>
        <h2>Dados do empréstimo/permuta</h2>
        <div className="grid">
          <div className="field">
            <label htmlFor="emp-direcao">Direção</label>
            <select id="emp-direcao" value={direcao} onChange={(e) => mudarDirecao(e.target.value as DirecaoEmprestimo)}>
              <option value="saida">{DIRECAO_LABEL.saida}</option>
              <option value="entrada">{DIRECAO_LABEL.entrada}</option>
            </select>
          </div>
          <div className="field">
            <label htmlFor="emp-unidade">
              Unidade de origem <span className="req">*</span>
            </label>
            <input
              id="emp-unidade"
              type="text"
              placeholder="ex.: Hospital Regional X"
              value={unidadeOrigem}
              onChange={(e) => setUnidadeOrigem(e.target.value)}
              required
            />
          </div>
          <div className="field">
            <label htmlFor="emp-oficio">
              Nº do ofício <span className="tag">opcional</span>
            </label>
            <input id="emp-oficio" type="text" value={numeroOficio} onChange={(e) => setNumeroOficio(e.target.value)} />
          </div>
        </div>

        <h2 style={{ marginTop: 22 }}>Itens</h2>
        <SeletorItensEntrada
          idBusca="emp-busca-item"
          itensDisponiveis={itens}
          carregandoItens={carregandoItens}
          linhas={linhas}
          aoMudarLinhas={setLinhas}
          mostrarCamposLote={direcao === 'entrada'}
        />

        <div className="actions">
          <button type="submit" className="btn" disabled={enviando}>
            {enviando ? 'Registrando…' : 'Confirmar registro'}
          </button>
        </div>
      </form>

      <div className="panel">
        <h2>Histórico</h2>
        {erroHistorico && <Alerta tipo="erro">{erroHistorico}</Alerta>}
        {carregandoHistorico && <p className="carregando">Carregando…</p>}
        {!carregandoHistorico && (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Data</th>
                  <th>Direção</th>
                  <th>Unidade</th>
                  <th>Ofício</th>
                  <th>Itens</th>
                </tr>
              </thead>
              <tbody>
                {historico.length === 0 && (
                  <tr>
                    <td colSpan={5} className="vazio-tabela">
                      Nenhum empréstimo/permuta registrado.
                    </td>
                  </tr>
                )}
                {historico.map((emp) => (
                  <tr key={emp.id}>
                    <td className="mono">{formatarDataHora(emp.data_hora)}</td>
                    <td>
                      <span className={`pill ${emp.direcao === 'entrada' ? 'ok' : 'roxo'}`}>{DIRECAO_LABEL[emp.direcao]}</span>
                    </td>
                    <td>{emp.unidade_origem}</td>
                    <td>{emp.numero_oficio ?? '—'}</td>
                    <td className="itens-resumo">{itensResumo(emp)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}
