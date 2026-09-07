"""
Temperatura de superfície (LST) mensal, 2001-2025.

Constrói uma tabela com a temperatura de superfície média — dia e noite,
separadas — de cada célula da grade de 1 km, para cada um dos 300 meses
entre janeiro de 2001 e dezembro de 2025. Exporta como CSV pro Google Drive
(a exportação é assíncrona: o script termina antes do arquivo existir de
fato, por isso ele fica esperando e checando o status da task).

Por que guardar dia E noite: a LST noturna é a melhor métrica de ilha de
calor urbana (mede o quanto o concreto retém calor acumulado ao longo do
dia); a diurna é mais dramática visualmente. As duas ficam salvas, e a
escolha de qual usar é feita na visualização.
"""

import time

import ee

from mapa_amazonia.config import (
    ANO_FIM,
    ANO_INICIO,
    BBOX,
    COLECAO_LST,
    DIR_RAW,
    EE_PROJECT_ID,
    ESCALA_LST,
    RESOLUCAO_M,
    ZERO_ABSOLUTO,
)
from mapa_amazonia.grade import construir_grade

NOME_ARQUIVO = "lst_mensal_2001_2025"


def mascarar_por_qc(imagem: ee.Image, banda_dado: str, banda_qc: str) -> ee.Image:
    """
    QC_Day/QC_Night guardam a qualidade do pixel dentro de um número
    inteiro, em bits (não em colunas separadas). Os dois bits menos
    significativos são a "flag obrigatória" do produto MODIS:

        00 (0) = LST produzida, boa qualidade
        01 (1) = LST produzida, qualidade "outra" (recomenda checar QA
                 detalhada — mas o valor existe e é utilizável)
        10 (2) = LST NÃO produzida, por causa de nuvem
        11 (3) = LST NÃO produzida, por outro motivo

    `bitwiseAnd(3)` (3 = 0b11) isola esses dois bits, ignorando todo o
    resto do número. Mantemos os pixels com flag 0 OU 1 (`.lt(2)` — "menor
    que 2" cobre exatamente {0, 1}) e descartamos 2 e 3, que são os únicos
    valores em que a LST realmente **não foi produzida**.

    Simplificação assumida aqui: só a flag obrigatória é checada (não os
    bits de erro de emissividade/LST, nos bits 6-7). Fica registrado como
    possível refinamento futuro.
    """
    qc = imagem.select(banda_qc)
    lst_foi_produzida = qc.bitwiseAnd(3).lt(2)
    return imagem.select(banda_dado).updateMask(lst_foi_produzida)


def mascarar_composicao(imagem: ee.Image) -> ee.Image:
    """Aplica a máscara de qualidade às duas bandas de uma composição de 8 dias."""
    dia = mascarar_por_qc(imagem, "LST_Day_1km", "QC_Day")
    noite = mascarar_por_qc(imagem, "LST_Night_1km", "QC_Night")
    return dia.addBands(noite)


def construir_imagem_mensal(data_inicio: ee.Date, regiao: ee.Geometry) -> ee.Image:
    """
    Filtra o MOD11A2 para as composições de 8 dias que caem dentro do mês
    que começa em `data_inicio`, mascara cada uma por qualidade, e tira a
    média temporal (`.mean()`) — pixels mascarados não entram na média.
    Depois converte de "Kelvin x 50" para Celsius (fator de escala e zero
    absoluto vêm do config.py).
    """
    data_fim = data_inicio.advance(1, "month")
    colecao_do_mes = (
        ee.ImageCollection(COLECAO_LST)
        .filterDate(data_inicio, data_fim)
        .filterBounds(regiao)
        .map(mascarar_composicao)
    )
    media_bruta = colecao_do_mes.mean()
    return media_bruta.multiply(ESCALA_LST).subtract(ZERO_ABSOLUTO)


def tabela_do_mes(
    data_inicio: ee.Date, grade: ee.FeatureCollection, regiao: ee.Geometry
) -> ee.FeatureCollection:
    """
    Reduz a imagem mensal (duas bandas: LST_Day_1km, LST_Night_1km, já em
    Celsius) a uma linha por célula da grade, com a média espacial de cada
    banda dentro da célula. `ano`/`mes` são gravados em cada linha para a
    tabela final conseguir distinguir os 300 meses depois do flatten.
    """
    imagem = construir_imagem_mensal(data_inicio, regiao)
    tabela = imagem.reduceRegions(
        collection=grade, reducer=ee.Reducer.mean(), scale=RESOLUCAO_M
    )
    ano = data_inicio.get("year")
    mes = data_inicio.get("month")
    return tabela.map(lambda celula: celula.set({"ano": ano, "mes": mes}))


def construir_tabela_completa(
    grade: ee.FeatureCollection, regiao: ee.Geometry
) -> ee.FeatureCollection:
    """
    Gera a lista dos 300 primeiros dias de cada mês entre ANO_INICIO e
    ANO_FIM (via `ee.List.sequence` + `.advance()`, inteiramente do lado do
    servidor — sem loop Python), aplica `tabela_do_mes` a cada uma, e achata
    (`.flatten()`) as 300 tabelas resultantes (uma por mês) numa só.
    """
    n_meses = (ANO_FIM - ANO_INICIO + 1) * 12
    data_inicial = ee.Date.fromYMD(ANO_INICIO, 1, 1)
    lista_datas = ee.List.sequence(0, n_meses - 1).map(
        lambda i: data_inicial.advance(i, "month")
    )
    lista_de_tabelas = lista_datas.map(
        lambda data: tabela_do_mes(ee.Date(data), grade, regiao)
    )
    return ee.FeatureCollection(lista_de_tabelas).flatten()


def validar_contra_calculo_unico(grade: ee.FeatureCollection, regiao: ee.Geometry) -> None:
    """
    Checagem de sanidade antes de gastar cota rodando os 300 meses: refaz
    só julho de 2020 pela grade (célula a célula, depois em média) e
    compara com o valor obtido calculando o bbox inteiro de uma vez
    (29.41 °C). Não precisam bater exatamente — a grade discretiza o bbox
    em retângulos de 1 km, então há uma pequena diferença de arredondamento
    esperada nas bordas — mas devem ficar próximos.
    """
    tabela_julho_2020 = tabela_do_mes(ee.Date("2020-07-01"), grade, regiao)
    media_dia = tabela_julho_2020.aggregate_mean("LST_Day_1km").getInfo()
    print(
        f"Validação — média por grade em julho/2020: {media_dia:.2f} °C "
        f"(bbox inteiro de uma vez: 29.41 °C)"
    )


def exportar(tabela: ee.FeatureCollection) -> ee.batch.Task:
    tarefa = ee.batch.Export.table.toDrive(
        collection=tabela,
        description="mapa_amazonia_lst_mensal",
        fileNamePrefix=NOME_ARQUIVO,
        fileFormat="CSV",
        selectors=["cell_id", "lon", "lat", "ano", "mes", "LST_Day_1km", "LST_Night_1km"],
    )
    tarefa.start()
    return tarefa


def acompanhar(tarefa: ee.batch.Task) -> None:
    """
    A exportação roda no servidor do Google, não aqui — este script só
    pergunta o status de tempos em tempos (`tarefa.status()`) até a task
    sair de RUNNING/READY. Substitui o "painel de Tasks" do Code Editor
    (https://code.earthengine.google.com/tasks): a mesma informação, só que
    consultada por código em vez de olhada num navegador.
    """
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
    print(f"Células na grade: {grade.size().getInfo()}")

    validar_contra_calculo_unico(grade, regiao)

    tabela = construir_tabela_completa(grade, regiao)
    tarefa = exportar(tabela)
    print(f"Task iniciada: {tarefa.id}")
    print(f"Vai cair no Google Drive (raiz) como '{NOME_ARQUIVO}.csv' quando terminar.")
    acompanhar(tarefa)
    print(f"Concluído. Baixe '{NOME_ARQUIVO}.csv' do Drive para {DIR_RAW}/ antes de rodar 05_montar_tabelas.py.")


if __name__ == "__main__":
    main()
