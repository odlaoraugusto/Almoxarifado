import { useState } from 'react';
import type { FormEvent } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { mensagemErro } from '../lib/api';
import { Alerta } from '../components/Alerta';
import { HOSPITAL, ORGANIZACAO } from '../lib/instituicao';

/** Login da equipe do almoxarifado (1 coordenador + 4 atendentes) —
 * único login do sistema, já que o pedido de material é público. Passo
 * único (sem seleção de unidade, diferente da farmácia): entra e vai
 * direto pro painel, com a troca de senha obrigatória sendo resolvida
 * pela rota protegida (ExigeSenhaAtualizada), não aqui. */
export function LoginPage() {
  const { token, usuario, entrar } = useAuth();

  const [login, setLogin] = useState('');
  const [senha, setSenha] = useState('');
  const [entrando, setEntrando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  if (token && usuario) {
    return <Navigate to="/painel" replace />;
  }

  async function aoSubmeter(e: FormEvent) {
    e.preventDefault();
    setErro(null);
    setEntrando(true);
    try {
      await entrar(login.trim(), senha);
    } catch (err) {
      setErro(mensagemErro(err, 'Login ou senha inválidos.'));
    } finally {
      setEntrando(false);
    }
  }

  return (
    <div className="login-wrap">
      <div className="login-split">
        <div className="login-brand">
          <div>
            <div className="login-brand-mark">
              <svg className="ic">
                <use href="#i-package" />
              </svg>
            </div>
            <h2>Solicitação de materiais do almoxarifado</h2>
            <p>Acesso restrito à equipe do almoxarifado — coordenador e atendentes.</p>
          </div>
          <div className="login-brand-foot">
            {ORGANIZACAO} · {HOSPITAL}
          </div>
          <div className="login-brand-ribbon" />
        </div>

        <div className="login-form-side">
          <div className="login-panels">
            <span className="login-step">ALMOXARIFADO</span>
            <div className="screen-head">
              <h1>Acesso da equipe</h1>
            </div>
            <form className="panel" onSubmit={aoSubmeter}>
              <h2>Login</h2>
              {erro && <Alerta tipo="erro">{erro}</Alerta>}
              <div className="field">
                <label htmlFor="login">
                  Login <span className="req">*</span>
                </label>
                <input
                  id="login"
                  type="text"
                  placeholder="usuario.nome"
                  value={login}
                  onChange={(e) => setLogin(e.target.value)}
                  autoComplete="username"
                  required
                />
              </div>
              <div className="field" style={{ marginTop: 12 }}>
                <label htmlFor="senha">
                  Senha <span className="req">*</span>
                </label>
                <input
                  id="senha"
                  type="password"
                  placeholder="••••••••"
                  value={senha}
                  onChange={(e) => setSenha(e.target.value)}
                  autoComplete="current-password"
                  required
                />
              </div>
              <div className="actions">
                <button type="submit" className="btn" disabled={entrando}>
                  <svg className="ic">
                    <use href="#i-key" />
                  </svg>
                  {entrando ? 'Entrando…' : 'Entrar'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
