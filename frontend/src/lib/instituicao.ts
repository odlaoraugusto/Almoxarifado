/** Identidade institucional — lida de variáveis de ambiente (`VITE_*`),
 * nunca hardcoded no código-fonte: o repositório é público e o nome real
 * da instituição não deve ficar commitado (mesmo princípio já aplicado
 * no backend com `HOSPITAL_NOME`/`HOSPITAL_ORGANIZACAO`, ver
 * `backend/app/core/config.py`). Configure os valores reais em `.env`
 * (gitignored) local ou nas variáveis de ambiente do deploy (Vercel).
 * Paleta oficial FESFSUS suavizada no resto do sistema (ver docs/
 * 00_PROJETO_ALMOXARIFADO.md, seção 1, e o protótipo aprovado do
 * formulário público). */
export const ORGANIZACAO = import.meta.env.VITE_ORGANIZACAO ?? 'Rede de Saúde Exemplo';
export const HOSPITAL = import.meta.env.VITE_HOSPITAL_NOME ?? 'Hospital Exemplo';
export const HOSPITAL_SIGLA = import.meta.env.VITE_HOSPITAL_SIGLA ?? 'ALMOX';
