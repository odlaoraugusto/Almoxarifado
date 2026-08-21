import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

/** Guarda de rota: exige token válido antes de renderizar qualquer tela
 * interna (painel, estoque, relatórios, usuários, trocar senha). */
export function RotaProtegida() {
  const { carregandoSessao, token } = useAuth();

  if (carregandoSessao) {
    return <p className="carregando" style={{ padding: 24 }}>Carregando sessão…</p>;
  }

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}

/** Segunda guarda, aplicada só às telas "normais" (dentro do Layout):
 * se o usuário ainda precisa trocar a senha padrão, força a passagem por
 * /trocar-senha antes de liberar o resto do sistema. A própria rota
 * /trocar-senha fica FORA desta guarda (senão nunca seria alcançável). */
export function ExigeSenhaAtualizada() {
  const { precisaTrocarSenha } = useAuth();

  if (precisaTrocarSenha) {
    return <Navigate to="/trocar-senha" replace />;
  }

  return <Outlet />;
}
