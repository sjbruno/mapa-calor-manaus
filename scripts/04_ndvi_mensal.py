"""
NDVI (índice de vegetação) mensal, na mesma grade da LST.

Constrói a camada de vegetação: NDVI médio mensal por célula da grade de
1 km, 2001-2025 — mesma grade, mesmos cell_id de 03_lst_mensal.py, pra que
o cruzamento temperatura×vegetação seja um join simples por célula.
Estrutura do script é deliberadamente paralela à de 03_lst_mensal.py.
"""

import time

import ee

from mapa_amazonia.config import (
    ANO_FIM,
    ANO_INICIO,
    BANDA_AGUA,
    BBOX,
    COLECAO_AGUA,
    COLECAO_NDVI,
    DIR_RAW,
    EE_PROJECT_ID,
    ESCALA_NDVI,
    LIMIAR_OCCURRENCE_AGUA,
    RESOLUCAO_NDVI_NATIVA_M,
)
from mapa_amazonia.grade import construir_grade

NOME_ARQUIVO = "ndvi_mensal_2001_2025"


def construir_mascara_agua(regiao: ee.Geometry) -> ee.Image:
    """
    Pixel é "água" se apareceu como água em pelo menos LIMIAR_OCCURRENCE_AGUA%
    dos anos observados pelo JRC Global Surface Water (1984-2021). Sem isso,
    o Rio Negro (NDVI negativo, água não é vegetação) puxaria pra baixo a
    média de qualquer célula que o contivesse — apareceria como "área
    degradada" no mapa, o que seria simplesmente errado.

    A banda "occurrence" já vem mascarada (sem valor) onde nunca houve água
    — por isso `unmask(0)`: onde o JRC não tem registro nenhum de água,
    tratamos como 0% (nunca foi água), não como "sem informação".
    """
    occurrence = ee.Image(COLECAO_AGUA).select(BANDA_AGUA).clip(regiao).unmask(0)
    return occurrence.gte(LIMIAR_OCCURRENCE_AGUA)


def mascarar_composicao(imagem: ee.Image, e_agua: ee.Image) -> ee.Image:
    """
    SummaryQA do MOD13Q1 é bem mais simples que o QC bit a bit de 03_lst_mensal.py:
    já vem como um número pequeno direto (0=ótimo, 1=bom, 2=nuvem/neve,
    3=inválido) — não precisa de bitwiseAnd, só comparar.

    A conversão de escala (NDVI vem como inteiro; 8000 = 0.8) acontece aqui,
    antes de aplicar as máscaras — mesma lógica de 03_lst_mensal.py: fazer a
    conversão uma vez só, num lugar central, com a constante do config.py.
    """
    qualidade_ok = imagem.select("SummaryQA").lte(1)
    ndvi = imagem.select("NDVI").multiply(ESCALA_NDVI)
    return ndvi.updateMask(qualidade_ok).updateMask(e_agua.Not())


def construir_imagem_mensal(
    data_inicio: ee.Date, regiao: ee.Geometry, e_agua: ee.Image
) -> ee.Image:
    """
    Mesma ideia de 03_lst_mensal.py, com MOD13Q1 (composições de 16 dias, não 8) —
    um mês normal contém ~2 composições. `.mean()` colapsa as que caírem no
    mês numa imagem só; pixels mascarados (nuvem, água) não entram na média.
    """
    data_fim = data_inicio.advance(1, "month")
    colecao_do_mes = (
        ee.ImageCollection(COLECAO_NDVI)
        .filterDate(data_inicio, data_fim)
        .filterBounds(regiao)
        .map(lambda imagem: mascarar_composicao(imagem, e_agua))
    )
    return colecao_do_mes.mean()


def tabela_do_mes(
    data_inicio: ee.Date, grade: ee.FeatureCollection, regiao: ee.Geometry, e_agua: ee.Image
) -> ee.FeatureCollection:
    """
    `scale=RESOLUCAO_NDVI_NATIVA_M` (250, não 1000): reduceRegions precisa da
    resolução NATIVA da imagem de entrada pra amostrar todos os pixels de
    250 m dentro de cada célula de 1 km corretamente — usar 1000 aqui
    faria o Earth Engine subamostrar (pular pixels), em vez de agregar todos.
    Isso substitui a necessidade de um `reduceResolution` explícito.

    `.setOutputs(["NDVI"])`: por padrão, quando a imagem de entrada tem uma
    banda só, `reduceRegions` nomeia a coluna de saída pelo **redutor**
    ("mean"), não pela banda — diferente de 03_lst_mensal.py, onde a imagem
    tinha 2 bandas (LST_Day_1km, LST_Night_1km) e cada uma virou sua própria
    coluna automaticamente. `setOutputs` força o nome da coluna, pra não
    depender dessa diferença de comportamento entre imagem de 1 banda e de
    várias.
    """
    imagem = construir_imagem_mensal(data_inicio, regiao, e_agua)
    tabela = imagem.reduceRegions(
        collection=grade,
        reducer=ee.Reducer.mean().setOutputs(["NDVI"]),
        scale=RESOLUCAO_NDVI_NATIVA_M,
    )
    ano = data_inicio.get("year")
    mes = data_inicio.get("month")
    return tabela.map(lambda celula: celula.set({"ano": ano, "mes": mes}))


def construir_tabela_completa(
    grade: ee.FeatureCollection, regiao: ee.Geometry, e_agua: ee.Image
) -> ee.FeatureCollection:
    n_meses = (ANO_FIM - ANO_INICIO + 1) * 12
    data_inicial = ee.Date.fromYMD(ANO_INICIO, 1, 1)
    lista_datas = ee.List.sequence(0, n_meses - 1).map(
        lambda i: data_inicial.advance(i, "month")
    )
    lista_de_tabelas = lista_datas.map(
        lambda data: tabela_do_mes(ee.Date(data), grade, regiao, e_agua)
    )
    return ee.FeatureCollection(lista_de_tabelas).flatten()


def validar(grade: ee.FeatureCollection, regiao: ee.Geometry, e_agua: ee.Image) -> None:
    """
    Checagem de sanidade antes de exportar os 300 meses: uma célula sobre a
    Reserva Ducke (floresta preservada) deve dar NDVI alto (~0.85); uma sobre
    o Centro deve dar bem mais baixo (~0.3 ou menos). Usa os
    PONTOS_REFERENCIA já definidos no config.py.
    """
    from mapa_amazonia.config import PONTOS_REFERENCIA

    tabela_julho_2020 = tabela_do_mes(ee.Date("2020-07-01"), grade, regiao, e_agua)

    for nome, (lat, lon) in PONTOS_REFERENCIA.items():
        ponto = ee.Geometry.Point([lon, lat])
        celula_mais_proxima = tabela_julho_2020.filterBounds(ponto).first()
        ndvi = celula_mais_proxima.get("NDVI").getInfo()
        print(f"  {nome}: NDVI = {ndvi:.3f}" if ndvi is not None else f"  {nome}: sem célula/dado aqui")


def exportar(tabela: ee.FeatureCollection) -> ee.batch.Task:
    tarefa = ee.batch.Export.table.toDrive(
        collection=tabela,
        description="mapa_amazonia_ndvi_mensal",
        fileNamePrefix=NOME_ARQUIVO,
        fileFormat="CSV",
        selectors=["cell_id", "lon", "lat", "ano", "mes", "NDVI"],
    )
    tarefa.start()
    return tarefa


def acompanhar(tarefa: ee.batch.Task) -> None:
    while True:
        status = tarefa.status()
        estado = status["state"]
        print(f"Status da task: {estado}")
        if estado in ("COMPLETED", "FAILED", "CANCELLED"):
            if estado == "FAILED":
                print("Erro:", status.get("error_message"))
            break
        time.sleep(30)


def main() -> None:
    ee.Initialize(project=EE_PROJECT_ID)

    regiao = ee.Geometry.Rectangle(BBOX)
    grade = construir_grade()
    e_agua = construir_mascara_agua(regiao)

    print("Validação — NDVI em julho/2020 nos pontos de referência:")
    validar(grade, regiao, e_agua)

    tabela = construir_tabela_completa(grade, regiao, e_agua)
    tarefa = exportar(tabela)
    print(f"Task iniciada: {tarefa.id}")
    print(f"Vai cair no Google Drive (raiz) como '{NOME_ARQUIVO}.csv' quando terminar.")
    acompanhar(tarefa)
    print(f"Concluído: {NOME_ARQUIVO}.csv")


if __name__ == "__main__":
    main()
