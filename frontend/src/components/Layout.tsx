import { NavLink, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { permissoesDe } from '../lib/permissoes';
import { labelPerfil } from '../lib/formato';
import { HOSPITAL, ORGANIZACAO } from '../lib/instituicao';

/** Casca da aplicação pós-login: barra institucional no topo (cores
 * cheias da marca FESFSUS) + sidebar de navegação + conteúdo da tela.
 * Itens de menu sem permissão somem da lista (não aparecem
 * desabilitados). */
export function Layout() {
  const { usuario, matrizPermissoes, sair } = useAuth();
  const permissoes = permissoesDe(usuario, matrizPermissoes);

  return (
    <div className="shell">
      <div className="topbar">
        <div className="inst-id">
          <span className="inst-org">{ORGANIZACAO}</span>
          <span className="inst-hospital">{HOSPITAL}</span>
        </div>
        <span className="inst-div" />
        <span className="inst-app">Almoxarifado</span>
      </div>

      <div className="app">
        <aside className="sidebar">
          <div className="brand">
            <div className="mark">Ax</div>
            <div className="name">
              Almoxarifado
              <small>controle de estoque</small>
            </div>
          </div>

          <div className="session-card">
            <div className="who">{usuario?.nome}</div>
            <div className="role">{usuario ? labelPerfil(usuario.perfil) : ''}</div>
            <div className="sair" style={{ display: 'flex', justifyContent: 'space-between', marginTop: 8 }}>
              <NavLink to="/trocar-senha" className="link-btn">
                Trocar senha
              </NavLink>
              <button type="button" className="link-btn" onClick={sair}>
                Sair
              </button>
            </div>
          </div>

          <nav className="screens" aria-label="Telas do sistema">
            <div className="eyebrow">Telas</div>
            <NavLink to="/painel" className="nav-btn">
              <span className="ic">▤</span>
              <span className="lbl">Painel de pedidos</span>
            </NavLink>
            <NavLink to="/estoque" className="nav-btn">
              <span className="ic">⛁</span>
              <span className="lbl">Estoque</span>
            </NavLink>
            <NavLink to="/entrada-compra" className="nav-btn">
              <span className="ic">⇢</span>
              <span className="lbl">Entrada por Compra</span>
            </NavLink>
            <NavLink to="/emprestimos" className="nav-btn">
              <span className="ic">⇄</span>
              <span className="lbl">Empréstimos/Permutas</span>
            </NavLink>
            {permissoes.descarteVencimento && (
              <NavLink to="/saida" className="nav-btn">
                <span className="ic">⇠</span>
                <span className="lbl">Saída</span>
              </NavLink>
            )}
            {permissoes.gerenciarSetores && (
              <NavLink to="/setores" className="nav-btn">
                <span className="ic">◫</span>
                <span className="lbl">Setores</span>
              </NavLink>
            )}
            <NavLink to="/relatorios" className="nav-btn">
              <span className="ic">▦</span>
              <span className="lbl">Relatórios</span>
            </NavLink>
            {permissoes.gestaoUsuarios && (
              <NavLink to="/usuarios" className="nav-btn">
                <span className="ic">⚉</span>
                <span className="lbl">Usuários</span>
              </NavLink>
            )}
            {permissoes.gerenciarPermissoes && (
              <NavLink to="/permissoes" className="nav-btn">
                <span className="ic">🛡</span>
                <span className="lbl">Permissões</span>
              </NavLink>
            )}
          </nav>

          <div className="sidebar-foot">{usuario?.login}</div>
        </aside>

        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
