"""
Download de arquivos do Google Drive da conta que autenticou o Earth Engine.

As exportações do Earth Engine (`Export.table.toDrive`, `Export.image.toDrive`)
caem no Google Drive, não em disco local — este módulo fecha esse último
passo, buscando um arquivo pelo nome e baixando pra `data/raw/`.

Não usa nenhuma dependência nova: `google-api-python-client` e `google-auth`
já vêm junto do `earthengine-api` (ver pyproject.toml / uv.lock). A
credencial reaproveitada é a mesma que `earthengine authenticate` já criou —
ela pediu escopo de Drive completo (`.../auth/drive`) desde a autorização
original na Fase 2, então não é preciso autenticar de novo.
"""

import io
from pathlib import Path

import ee.data
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload


def baixar_do_drive(nome_arquivo: str, pasta_destino: Path) -> Path:
    """
    Busca `nome_arquivo` no Google Drive da conta autenticada e baixa pra
    dentro de `pasta_destino`, com o mesmo nome. Devolve o caminho local.

    Assume que `ee.Initialize(...)` já foi chamado antes (é de lá que vem a
    credencial reaproveitada).
    """
    credenciais = ee.data.get_persistent_credentials()
    servico = build("drive", "v3", credentials=credenciais)

    busca = servico.files().list(
        q=f"name = '{nome_arquivo}' and trashed = false",
        fields="files(id, name, modifiedTime)",
        orderBy="modifiedTime desc",
        pageSize=1,
    ).execute()

    arquivos = busca.get("files", [])
    if not arquivos:
        raise FileNotFoundError(
            f"'{nome_arquivo}' não encontrado no Google Drive da conta autenticada."
        )

    arquivo_id = arquivos[0]["id"]

    pasta_destino.mkdir(parents=True, exist_ok=True)
    caminho_local = pasta_destino / nome_arquivo

    requisicao = servico.files().get_media(fileId=arquivo_id)
    buffer = io.FileIO(caminho_local, "wb")
    downloader = MediaIoBaseDownload(buffer, requisicao)

    concluido = False
    while not concluido:
        _, concluido = downloader.next_chunk()

    return caminho_local
