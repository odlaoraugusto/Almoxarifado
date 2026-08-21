"""Geração de arquivos (PDF/Excel) dos relatórios.

Módulo isolado dos services de domínio: `RelatorioService` continua
responsável só pelos dados; aqui só se resolve "dados já prontos ->
arquivo para download", reaproveitando o mesmo `RelatorioMetadados`
(cabeçalho institucional) que já existe em toda resposta de
`/relatorios/*`.
"""
