import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ExigeSenhaAtualizada, RotaProtegida } from './components/RotaProtegida';
import { Layout } from './components/Layout';
import { PedidoPublicoPage } from './pages/PedidoPublicoPage';
import { LoginPage } from './pages/LoginPage';
import { TrocarSenhaPage } from './pages/TrocarSenhaPage';
import { PainelPage } from './pages/PainelPage';
import { EstoquePage } from './pages/EstoquePage';
import { SetoresPage } from './pages/SetoresPage';
import { RelatoriosPage } from './pages/RelatoriosPage';
import { UsuariosPage } from './pages/UsuariosPage';

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<PedidoPublicoPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route element={<RotaProtegida />}>
            <Route path="/trocar-senha" element={<TrocarSenhaPage />} />
            <Route element={<ExigeSenhaAtualizada />}>
              <Route element={<Layout />}>
                <Route path="/painel" element={<PainelPage />} />
                <Route path="/estoque" element={<EstoquePage />} />
                <Route path="/setores" element={<SetoresPage />} />
                <Route path="/relatorios" element={<RelatoriosPage />} />
                <Route path="/usuarios" element={<UsuariosPage />} />
              </Route>
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
