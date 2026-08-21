import { useState } from 'react';
import type { FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { mensagemErro } from '../lib/api';
import { Alerta } from '../components/Alerta';
import { HOSPITAL, ORGANIZACAO } from '../lib/instituicao';

/** Troca de senha — forçada no primeiro login (usuário novo ou com senha
 * resetada pelo Coordenador nasce com `deve_trocar_senha=true`) e também
 * acessível a qualquer momento pelo link "Trocar senha" no menu lateral. */
export function TrocarSenhaPage() {
  const { usuario, precisaTrocarSenha, trocarSenha } = useAuth();
  const navigate = useNavigate();

  const [senhaAtual, setSenhaAtual] = useState('');
  const [senhaNova, setSenhaNova] = useState('');
  const [confirmarSenhaNova, setConfirmarSenhaNova] = useState('');
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [sucesso, setSucesso] = useState(false);

  async function aoSubmeter(e: FormEvent) {
    e.preventDefault();
    setErro(null);
    if (senhaNova !== confirmarSenhaNova) {
      setErro('A confirmação não confere com a nova senha.');
      return;
    }
    if (senhaNova.length < 8) {
      setErro('A nova senha precisa ter pelo menos 8 caracteres.');
      return;
    }
    setSalvando(true);
    try {
      await trocarSenha(senhaAtual, senhaNova);
      if (precisaTrocarSenha) {
        navigate('/painel', { replace: true });
      } else {
        setSucesso(true);
        setSenhaAtual('');
        setSenhaNova('');
        setConfirmarSenhaNova('');
      }
    } catch (err) {
      setErro(mensagemErro(err, 'Não foi possível trocar a senha.'));
    } finally {
      setSalvando(false);
    }
  }

  return (
    <div className="login-wrap">
      <div className="topbar">
        <div className="inst-id">
          <span className="inst-org">{ORGANIZACAO}</span>
          <span className="inst-hospital">{HOSPITAL}</span>
        </div>
        <span className="inst-div" />
        <span className="inst-app">Almoxarifado</span>
      </div>

      <div className="login-main">
        <div className="login-panels">
          <div className="screen-head">
            <h1>Trocar senha</h1>
            <span className="screen-tag">{precisaTrocarSenha ? 'obrigatório no primeiro acesso' : 'opcional'}</span>
          </div>
          <p className="screen-sub">
            {precisaTrocarSenha
              ? 'Sua senha ainda é a padrão/temporária definida pelo Coordenador — cadastre uma nova antes de continuar.'
              : `Olá, ${usuario?.nome ?? ''}. Defina uma nova senha quando quiser.`}
          </p>

          <form className="panel" onSubmit={aoSubmeter}>
            <h2>Nova senha</h2>
            {erro && <Alerta tipo="erro">{erro}</Alerta>}
            {sucesso && <Alerta tipo="sucesso">Senha atualizada.</Alerta>}
            <div className="field">
              <label htmlFor="senha-atual">
                Senha atual <span className="req">*</span>
              </label>
              <input
                id="senha-atual"
                type="password"
                value={senhaAtual}
                onChange={(e) => setSenhaAtual(e.target.value)}
                autoComplete="current-password"
                required
              />
            </div>
            <div className="field" style={{ marginTop: 12 }}>
              <label htmlFor="senha-nova">
                Nova senha <span className="req">*</span>
              </label>
              <input
                id="senha-nova"
                type="password"
                placeholder="mínimo 8 caracteres"
                value={senhaNova}
                onChange={(e) => setSenhaNova(e.target.value)}
                autoComplete="new-password"
                required
              />
            </div>
            <div className="field" style={{ marginTop: 12 }}>
              <label htmlFor="confirmar-senha-nova">
                Confirmar nova senha <span className="req">*</span>
              </label>
              <input
                id="confirmar-senha-nova"
                type="password"
                value={confirmarSenhaNova}
                onChange={(e) => setConfirmarSenhaNova(e.target.value)}
                autoComplete="new-password"
                required
              />
            </div>
            <div className="actions">
              <button type="submit" className="btn" disabled={salvando}>
                {salvando ? 'Salvando…' : 'Trocar senha'}
              </button>
              {!precisaTrocarSenha && (
                <button type="button" className="btn ghost" onClick={() => navigate('/painel')}>
                  Voltar ao painel
                </button>
              )}
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
