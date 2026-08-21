"""Formato de exportação aceito pelos endpoints de relatório.

Query param opcional `formato` nos endpoints de `/relatorios/*`: ausente
(default) → resposta JSON de sempre; `pdf`/`excel` → arquivo para
download (`StreamingResponse`), reaproveitando a mesma checagem de
permissão e os mesmos filtros do endpoint JSON.
"""

import enum


class FormatoExportacao(str, enum.Enum):
    pdf = "pdf"
    excel = "excel"
