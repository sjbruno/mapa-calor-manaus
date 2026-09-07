"""
Deriva orbital do Terra: medir com dado direto do satélite.

Uma checagem de sanidade nos dados de LST encontrou 2025 anomalamente frio
em `lst_dia_c` (sem explicação de nuvem — a completude de dado está ótima).
A explicação: a NASA documenta que o satélite Terra vem passando cada vez
mais cedo sobre o equador desde 2020 (deriva orbital, sem mais manobras de
correção porque a missão está no fim). Passagem mais cedo fotografa a
superfície antes dela esquentar — viés de frio, crescente com o tempo.

Este script confirma isso com dado do próprio satélite, não por coincidência
de datas: o MOD11A2 (mesmo produto de 03_lst_mensal.py) já vem com uma banda
chamada `Day_view_time` — o horário local em que cada pixel foi medido.

Diferente dos scripts de LST/NDVI, isso não precisa da grade de 1 km nem de
exportação assíncrona pro Drive: é só a média do bbox inteiro, por mês — 300
números, não 612 mil linhas. Cabe num `.getInfo()` só, síncrono.
"""

import ee
import pandas as pd

from mapa_amazonia.config import (
    ANO_FIM,
    ANO_INICIO,
    BBOX,
    COLECAO_LST,
    DIR_PROCESSED,
    EE_PROJECT_ID,
)

NOME_ARQUIVO = "hora_passagem_mensal"

# Day_view_time/Night_view_time vêm em décimos de hora (bruto 105 = 10,5h).
ESCALA_HORA = 0.1


def _mascarar_por_qc(imagem: ee.Image, banda_dado: str, banda_qc: str) -> ee.Image:
    """Mesma regra de QC de `03_lst_mensal.py` — reaproveitada aqui porque
    o horário de um pixel só importa se aquele pixel também tiver LST
    válida (senão não entrou na média que queremos explicar)."""
    qc = imagem.select(banda_qc)
    lst_foi_produzida = qc.bitwiseAnd(3).lt(2)
    return imagem.select(banda_dado).updateMask(lst_foi_produzida)


def horario_medio_do_mes(data_inicio: ee.Date, regiao: ee.Geometry) -> ee.Feature:
    """
    Horário médio (hora decimal) de passagem de dia e de noite sobre o bbox
    inteiro, naquele mês — mesma máscara de QC de 03_lst_mensal.py, mesma
    composição mensal (`.mean()` das composições de 8 dias). `reduceRegion` (não
    `reduceRegions`): não precisamos de uma linha por célula aqui, só um
    número por mês pro bbox inteiro.
    """
    data_fim = data_inicio.advance(1, "month")
    colecao_do_mes = (
        ee.ImageCollection(COLECAO_LST).filterDate(data_inicio, data_fim).filterBounds(regiao)
    )

    hora_dia = (
        colecao_do_mes.map(lambda img: _mascarar_por_qc(img, "Day_view_time", "QC_Day"))
        .mean()
        .multiply(ESCALA_HORA)
        .rename("hora_dia")
    )
    hora_noite = (
        colecao_do_mes.map(lambda img: _mascarar_por_qc(img, "Night_view_time", "QC_Night"))
        .mean()
        .multiply(ESCALA_HORA)
        .rename("hora_noite")
    )

    valores = ee.Image.cat([hora_dia, hora_noite]).reduceRegion(
        reducer=ee.Reducer.mean(), geometry=regiao, scale=1000, maxPixels=1e9
    )
    return ee.Feature(None, valores).set(
        {"ano": data_inicio.get("year"), "mes": data_inicio.get("month")}
    )


def construir_tabela(regiao: ee.Geometry) -> ee.FeatureCollection:
    n_meses = (ANO_FIM - ANO_INICIO + 1) * 12
    data_inicial = ee.Date.fromYMD(ANO_INICIO, 1, 1)
    lista_datas = ee.List.sequence(0, n_meses - 1).map(lambda i: data_inicial.advance(i, "month"))
    lista_de_features = lista_datas.map(lambda data: horario_medio_do_mes(ee.Date(data), regiao))
    return ee.FeatureCollection(lista_de_features)


def main() -> None:
    ee.Initialize(project=EE_PROJECT_ID)
    regiao = ee.Geometry.Rectangle(BBOX)

    print("Calculando horário médio de passagem (dia e noite), 300 meses, num getInfo() só...")
    tabela = construir_tabela(regiao)
    info = tabela.getInfo()

    linhas = [f["properties"] for f in info["features"]]
    df = pd.DataFrame(linhas).sort_values(["ano", "mes"]).reset_index(drop=True)

    n_meses_esperado = (ANO_FIM - ANO_INICIO + 1) * 12
    assert len(df) == n_meses_esperado, f"{len(df)} meses, esperava {n_meses_esperado}."

    DIR_PROCESSED.mkdir(parents=True, exist_ok=True)
    caminho = DIR_PROCESSED / f"{NOME_ARQUIVO}.parquet"
    df.to_parquet(caminho, index=False)

    print(f"Salvo em {caminho} ({len(df)} meses).")
    print()
    print("Hora média de passagem diurna, por ano (média dos 12 meses):")
    print(df.groupby("ano")["hora_dia"].mean().round(3).to_string())


if __name__ == "__main__":
    main()
