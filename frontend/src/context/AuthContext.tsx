import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { api } from '../lib/api';
import type { PermissaoPerfil, TokenResponse, UsuarioMe } from '../types';

const CHAVE_TOKEN = 'almoxarifado_token';

interface AuthContextValue {
  carregandoSessao: boolean;
  token: string | null;
  usuario: UsuarioMe | null;
  /** Matriz configurável de `/permissoes` (Coordenador/Atendente) —
   * carregada junto da sessão, usada por `permissoesDe()`. */
  matrizPermissoes: PermissaoPerfil[] | null;
  precisaTrocarSenha: boolean;
  entrar: (login: string, senha: string) => Promise<void>;
  trocarSenha: (senhaAtual: string, senhaNova: string) => Promise<void>;
  /** Chamado pela tela de Permissões depois de salvar, pra refletir a
   * matriz nova sem precisar de um reload de página inteiro. */
  recarregarPermissoes: () => Promise<void>;
  sair: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [carregandoSessao, setCarregandoSessao] = useState(true);
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(CHAVE_TOKEN));
  const [usuario, setUsuario] = useState<UsuarioMe | null>(null);
  const [matrizPermissoes, setMatrizPermissoes] = useState<PermissaoPerfil[] | null>(null);

  const carregarPermissoes = useCallback(async (tok: string) => {
    const matriz = await api.get<PermissaoPerfil[]>('/permissoes', { token: tok });
    setMatrizPermissoes(matriz);
  }, []);

  useEffect(() => {
    if (!token) {
      setCarregandoSessao(false);
      return;
    }
    api
      .get<UsuarioMe>('/auth/me', { token })
      .then(async (dados) => {
        setUsuario(dados);
        await carregarPermissoes(token);
      })
      .catch(() => {
        localStorage.removeItem(CHAVE_TOKEN);
        setToken(null);
        setUsuario(null);
      })
      .finally(() => setCarregandoSessao(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const entrar = useCallback(
    async (login: string, senha: string) => {
      const resposta = await api.post<TokenResponse>('/auth/login', { login, senha });
      localStorage.setItem(CHAVE_TOKEN, resposta.access_token);
      setToken(resposta.access_token);
      const me = await api.get<UsuarioMe>('/auth/me', { token: resposta.access_token });
      setUsuario(me);
      await carregarPermissoes(resposta.access_token);
    },
    [carregarPermissoes],
  );

  const trocarSenha = useCallback(
    async (senhaAtual: string, senhaNova: string) => {
      await api.post('/auth/trocar-senha', { senha_atual: senhaAtual, senha_nova: senhaNova }, { token });
      // Backend não reemite token (o flag não vive no JWT) — atualiza só o
      // estado local, que é o que a rota protegida consulta pra decidir se
      // ainda precisa forçar a passagem por /trocar-senha.
      setUsuario((atual) => (atual ? { ...atual, deve_trocar_senha: false } : atual));
    },
    [token],
  );

  const recarregarPermissoes = useCallback(async () => {
    if (token) await carregarPermissoes(token);
  }, [token, carregarPermissoes]);

  const sair = useCallback(() => {
    localStorage.removeItem(CHAVE_TOKEN);
    setToken(null);
    setUsuario(null);
    setMatrizPermissoes(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      carregandoSessao,
      token,
      usuario,
      matrizPermissoes,
      precisaTrocarSenha: !!token && usuario?.deve_trocar_senha === true,
      entrar,
      trocarSenha,
      recarregarPermissoes,
      sair,
    }),
    [carregandoSessao, token, usuario, matrizPermissoes, entrar, trocarSenha, recarregarPermissoes, sair],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth precisa estar dentro de <AuthProvider>.');
  return ctx;
}
