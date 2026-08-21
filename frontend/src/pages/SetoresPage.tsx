import { useCallback, useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { useAuth } from '../context/AuthContext';
import { api, mensagemErro } from '../lib/api';
import { permissoesDe } from '../lib/permissoes';
import { Alerta } from '../components/Alerta';
import type { Setor } from '../types';

/** CRUD simples de setores solicitantes (doc, seção 3.4) — exclusivo do
 * Coordenador. Sem responsável fixo/centro de custo, só nome + ativo.
 * Alimenta o `<select>` do formulário público de pedido. */
export function SetoresPage() {
  const { usuario, token } = useAuth();
  const permissoes = permissoesDe(usuario);

  if (!permissoes.gerenciarSetores) {
    return (
      <section>
        <div className="screen-head">
          <h1>Setores</h1>
        </div>
        <div className="locked-panel">
          <span className="lock-icon">🔒</span>
          Cadastro de setores é exclusivo do Coordenador.
        </div>
      </section>
    );
  }

  return <GestaoSetores token={token} />;
}

function GestaoSetores({ token }: { token: string | null }) {
  const [setores, setSetores] = useState<Setor[]>([]);
  const [mostrarInativos, setMostrarInativos] = useState(false);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const [sucesso, setSucesso] = useState<string | null>(null);

  const [editandoId, setEditandoId] = useState<number | null>(null);
  const [nome, setNome] = useState('');
  const [enviando, setEnviando] = useState(false);

  const carregar = useCallback(() => {
    if (!token) return;
    setCarregando(true);
    api
      .get<Setor[]>('/setores', { token, params: { incluir_inativos: mostrarInativos } })
      .then(setSetores)
      .catch((err) => setErro(mensagemErro(err, 'Não foi possível carregar os setores.')))
      .finally(() => setCarregando(false));
  }, [token, mostrarInativos]);

  useEffect(() => {
    carregar();
  }, [carregar]);

  function iniciarEdicao(s: Setor) {
    setEditandoId(s.id);
    setNome(s.nome);
    setErro(null);
    setSucesso(null);
  }

  function cancelarEdicao() {
    setEditandoId(null);
    setNome('');
  }

  async function aoSubmeter(e: FormEvent) {
    e.preventDefault();
    setErro(null);
    setSucesso(null);
    setEnviando(true);
    try {
      if (editandoId == null) {
        await api.post('/setores', { nome: nome.trim() }, { token });
        setSucesso('Setor cadastrado.');
      } else {
        await api.put(`/setores/${editandoId}`, { nome: nome.trim() }, { token });
        setSucesso('Setor atualizado.');
      }
      cancelarEdicao();
      carregar();
    } catch (err) {
      setErro(mensagemErro(err, 'Não foi possível salvar o setor.'));
    } finally {
      setEnviando(false);
    }
  }

  async function alternarAtivo(s: Setor) {
    setErro(null);
    setSucesso(null);
    try {
      await api.put(`/setores/${s.id}`, { ativo: !s.ativo }, { token });
      setSucesso(s.ativo ? `${s.nome} desativado.` : `${s.nome} reativado.`);
      if (editandoId === s.id) cancelarEdicao();
      carregar();
    } catch (err) {
      setErro(mensagemErro(err, 'Não foi possível alterar o status do setor.'));
    }
  }

  return (
    <section>
      <div className="screen-head">
        <h1>Setores</h1>
        <span className="screen-tag">exclusivo Coordenador</span>
      </div>
      <p className="screen-sub">
        Setores que aparecem no formulário público de pedido de material. Desativar um setor não apaga o histórico
        de pedidos já feitos por ele — só some da lista de novos pedidos.
      </p>

      {erro && <Alerta tipo="erro">{erro}</Alerta>}
      {sucesso && <Alerta tipo="sucesso">{sucesso}</Alerta>}

      <form className="panel" onSubmit={aoSubmeter}>
        <h2>{editandoId == null ? 'Novo setor' : `Editando — ${nome}`}</h2>
        <div className="grid">
          <div className="field">
            <label htmlFor="setor-nome">
              Nome <span className="req">*</span>
            </label>
            <input
              id="setor-nome"
              type="text"
              placeholder="ex.: UTI Neonatal"
              value={nome}
              onChange={(e) => setNome(e.target.value)}
              required
            />
          </div>
        </div>
        <div className="actions">
          <button type="submit" className="btn" disabled={enviando || !nome.trim()}>
            {enviando ? 'Salvando…' : editandoId == null ? 'Cadastrar' : 'Salvar alterações'}
          </button>
          {editandoId != null && (
            <button type="button" className="btn ghost" onClick={cancelarEdicao}>
              Cancelar edição
            </button>
          )}
        </div>
      </form>

      <div className="panel">
        <h2 style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>Cadastrados</span>
          <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontWeight: 500, textTransform: 'none', fontSize: 12.5 }}>
            <input type="checkbox" checked={mostrarInativos} onChange={(e) => setMostrarInativos(e.target.checked)} />
            Mostrar inativos
          </label>
        </h2>
        {carregando && <p className="carregando">Carregando…</p>}
        {!carregando && (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Nome</th>
                  <th>Status</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {setores.length === 0 && (
                  <tr>
                    <td colSpan={3} className="vazio-tabela">
                      Nenhum setor cadastrado.
                    </td>
                  </tr>
                )}
                {setores.map((s) => (
                  <tr key={s.id}>
                    <td>{s.nome}</td>
                    <td>
                      <span className={`pill ${s.ativo ? 'ok' : 'muted'}`}>{s.ativo ? 'ativo' : 'inativo'}</span>
                    </td>
                    <td style={{ display: 'flex', gap: 6 }}>
                      <button type="button" className="btn ghost sm" onClick={() => iniciarEdicao(s)}>
                        Editar
                      </button>
                      <button type="button" className={`btn sm ${s.ativo ? 'danger' : 'ok'}`} onClick={() => alternarAtivo(s)}>
                        {s.ativo ? 'Desativar' : 'Reativar'}
                      </button>
                    </td>
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
