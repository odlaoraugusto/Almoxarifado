import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { permissoesDe } from '../lib/permissoes';
import { api, mensagemErro } from '../lib/api';
import { Alerta } from '../components/Alerta';
import type { PermissaoPerfil } from '../types';

type LinhaEditavel = Omit<PermissaoPerfil, 'perfil'>;

const LINHA_VAZIA: LinhaEditavel = {
  ajustar_estoque: false,
  gerenciar_itens: false,
  gerenciar_setores: false,
  gestao_usuarios: false,
  relatorio_movimentacoes: false,
  descarte_vencimento: false,
};

const ACOES: { chave: keyof LinhaEditavel; rotulo: string; ajuda: string }[] = [
  {
    chave: 'ajustar_estoque',
    rotulo: 'Ajustar estoque',
    ajuda: 'Corrigir saldo por contagem física, fora do fluxo normal de pedido/entrada.',
  },
  {
    chave: 'gerenciar_itens',
    rotulo: 'Gerenciar itens',
    ajuda: 'Cadastrar e editar itens do catálogo.',
  },
  {
    chave: 'gerenciar_setores',
    rotulo: 'Gerenciar setores',
    ajuda: 'Cadastrar os setores que podem abrir pedido no formulário público.',
  },
  {
    chave: 'gestao_usuarios',
    rotulo: 'Gestão de usuários',
    ajuda: 'Cadastrar, editar e desativar logins do almoxarifado (promover a Admin continua exclusivo do Admin).',
  },
  {
    chave: 'relatorio_movimentacoes',
    rotulo: 'Relatório de movimentações',
    ajuda: 'Ver a trilha de auditoria completa (todas as entradas/saídas/ajustes).',
  },
  {
    chave: 'descarte_vencimento',
    rotulo: 'Dar baixa por vencimento',
    ajuda: 'Registrar perda de lote vencido, reduzindo o saldo (trilha própria, separada de Ajuste de contagem física).',
  },
];

const PERFIS_CONFIGURAVEIS: { chave: 'coordenador' | 'atendente'; rotulo: string }[] = [
  { chave: 'coordenador', rotulo: 'Coordenador' },
  { chave: 'atendente', rotulo: 'Atendente' },
];

/** Tela exclusiva do Admin — decide o que Coordenador e Atendente podem
 * fazer além do básico (conferir pedido, registrar entrada/empréstimo,
 * ver estoque e relatório de pedidos, liberado a qualquer login). O
 * Admin não aparece na matriz: é superusuário implícito, sempre com
 * tudo liberado. */
export function PermissoesPage() {
  const { usuario, matrizPermissoes, token, recarregarPermissoes } = useAuth();
  const permissoes = permissoesDe(usuario, matrizPermissoes);

  if (!permissoes.gerenciarPermissoes) {
    return (
      <section>
        <div className="screen-head">
          <h1>Permissões</h1>
        </div>
        <div className="locked-panel">
          <span className="lock-icon">🔒</span>
          Gerenciar permissões é exclusivo do Admin.
        </div>
      </section>
    );
  }

  return <GestaoPermissoes token={token} matrizAtual={matrizPermissoes} recarregar={recarregarPermissoes} />;
}

function GestaoPermissoes({
  token,
  matrizAtual,
  recarregar,
}: {
  token: string | null;
  matrizAtual: PermissaoPerfil[] | null;
  recarregar: () => Promise<void>;
}) {
  const [form, setForm] = useState<Record<'coordenador' | 'atendente', LinhaEditavel>>({
    coordenador: LINHA_VAZIA,
    atendente: LINHA_VAZIA,
  });
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [sucesso, setSucesso] = useState<string | null>(null);

  useEffect(() => {
    if (!matrizAtual) return;
    setForm((atual) => {
      const proximo = { ...atual };
      for (const linha of matrizAtual) {
        if (linha.perfil === 'coordenador' || linha.perfil === 'atendente') {
          const { perfil: _perfil, ...resto } = linha;
          proximo[linha.perfil] = resto;
        }
      }
      return proximo;
    });
  }, [matrizAtual]);

  function alternar(perfil: 'coordenador' | 'atendente', chave: keyof LinhaEditavel) {
    setSucesso(null);
    setForm((atual) => ({
      ...atual,
      [perfil]: { ...atual[perfil], [chave]: !atual[perfil][chave] },
    }));
  }

  async function salvar() {
    setErro(null);
    setSucesso(null);
    setSalvando(true);
    try {
      await api.put('/permissoes', { coordenador: form.coordenador, atendente: form.atendente }, { token });
      await recarregar();
      setSucesso('Permissões atualizadas.');
    } catch (err) {
      setErro(mensagemErro(err, 'Não foi possível salvar as permissões.'));
    } finally {
      setSalvando(false);
    }
  }

  return (
    <section>
      <div className="screen-head">
        <h1>Permissões</h1>
        <span className="screen-tag">exclusivo Admin</span>
      </div>
      <p className="screen-sub">
        Define o que Coordenador e Atendente podem fazer além do básico (conferir pedido, registrar
        entrada/empréstimo, ver estoque e relatório de pedidos — liberado a qualquer login). O Admin sempre tem
        tudo liberado e não aparece nesta matriz.
      </p>

      {erro && <Alerta tipo="erro">{erro}</Alerta>}
      {sucesso && <Alerta tipo="sucesso">{sucesso}</Alerta>}

      <div className="panel">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Ação</th>
                {PERFIS_CONFIGURAVEIS.map((p) => (
                  <th key={p.chave} style={{ textAlign: 'center' }}>
                    {p.rotulo}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {ACOES.map((acao) => (
                <tr key={acao.chave}>
                  <td>
                    <div>{acao.rotulo}</div>
                    <div className="screen-sub" style={{ margin: 0, fontSize: 12 }}>
                      {acao.ajuda}
                    </div>
                  </td>
                  {PERFIS_CONFIGURAVEIS.map((p) => (
                    <td key={p.chave} style={{ textAlign: 'center' }}>
                      <input
                        type="checkbox"
                        checked={form[p.chave][acao.chave]}
                        onChange={() => alternar(p.chave, acao.chave)}
                      />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="actions" style={{ marginTop: 16 }}>
          <button type="button" className="btn" onClick={salvar} disabled={salvando}>
            {salvando ? 'Salvando…' : 'Salvar permissões'}
          </button>
        </div>
      </div>
    </section>
  );
}
