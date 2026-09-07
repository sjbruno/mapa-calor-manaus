"""
Monta as tabelas finais: junta LST + NDVI, limpa e exporta.

Transforma os dois CSVs crus (03_lst_mensal.py e 04_ndvi_mensal.py) nos
arquivos que o site vai efetivamente ler: um Parquet por ano com temperatura
e vegetação já juntas por célula/mês, e um `grade.geojson` com a geometria
das ~2.040 células (baixado do Earth Engine, já que os CSVs só têm o
centroide de cada célula, não o polígono inteiro).

Diferença deste script para os anteriores: não faz nenhuma conta nova no
Earth Engine sobre os dados numéricos (isso já foi feito e baixado). Só usa
o Earth Engine de novo para recuperar a geometria da grade.
"""

import json

import ee
import numpy as np
import pandas as pd

from mapa_amazonia.config import (
    ANO_FIM,
    ANO_INICIO,
    DIR_PROCESSED,
    DIR_RAW,
    EE_PROJECT_ID,
    LIMIAR_INVERSAO_NOITE_DIA_C,
    LIMIAR_Z_CLIMATOLOGICO,
    LST_MAX_C,
    LST_MIN_C,
    NDVI_MAX,
    NDVI_MIN,
)
from mapa_amazonia.grade import construir_grade

COLUNAS_LST = ["lst_dia_c", "lst_noite_c"]
COLUNA_NDVI = "ndvi"


def carregar_e_juntar() -> pd.DataFrame:
    """
    Junta as duas tabelas por (cell_id, ano, mes) — a chave que os dois
    scripts anteriores compartilham porque usaram a mesma grade (`grade.py`).
    `lon`/`lat` existem nos dois CSVs (mesma origem), então descartamos a
    cópia do NDVI e mantemos só a da LST, depois de conferir que são
    realmente iguais — não confiar que "vêm da mesma grade" é garantia
    automática de que os números batem (não confiar em comportamento
    implícito do Earth Engine).

    `how="outer"` + `indicator=True` em vez de `how="inner"`: um inner merge
    juntaria silenciosamente só o que bate e esconderia qualquer célula/mês
    que exista de um lado e não do outro. Com outer + indicator, uma
    divergência vira uma linha com `_merge != "both"` que o assert seguinte
    pega.
    """
    lst = pd.read_csv(DIR_RAW / "lst_mensal_2001_2025.csv")
    ndvi = pd.read_csv(DIR_RAW / "ndvi_mensal_2001_2025.csv")

    comparacao = lst.merge(ndvi, on=["cell_id", "ano", "mes"], suffixes=("", "_ndvi"))
    coordenadas_batem = np.allclose(comparacao["lon"], comparacao["lon_ndvi"]) and np.allclose(
        comparacao["lat"], comparacao["lat_ndvi"]
    )
    assert coordenadas_batem, (
        "lon/lat de LST e NDVI divergem para o mesmo cell_id — os scripts de "
        "LST e NDVI não usaram a mesma grade?"
    )

    ndvi_sem_coordenadas = ndvi.drop(columns=["lon", "lat"])
    tabela = lst.merge(
        ndvi_sem_coordenadas, on=["cell_id", "ano", "mes"], how="outer", indicator=True
    )

    apenas_de_um_lado = tabela[tabela["_merge"] != "both"]
    assert apenas_de_um_lado.empty, (
        f"{len(apenas_de_um_lado)} linhas existem só em LST ou só em NDVI "
        "— os dois scripts deveriam ter processado exatamente a mesma "
        "grade e o mesmo período."
    )
    tabela = tabela.drop(columns=["_merge"])

    n_celulas = tabela["cell_id"].nunique()
    n_meses = (ANO_FIM - ANO_INICIO + 1) * 12
    esperado = n_celulas * n_meses
    assert len(tabela) == esperado, (
        f"{len(tabela)} linhas, esperava {esperado} "
        f"({n_celulas} células x {n_meses} meses)."
    )
    assert not tabela.duplicated(subset=["cell_id", "ano", "mes"]).any(), (
        "cell_id + ano + mes deveria ser uma chave única — há duplicata."
    )

    return tabela.rename(
        columns={
            "LST_Day_1km": "lst_dia_c",
            "LST_Night_1km": "lst_noite_c",
            "NDVI": "ndvi",
        }
    )


def aplicar_faixas_plausiveis(tabela: pd.DataFrame) -> pd.DataFrame:
    """
    Qualquer valor fora da faixa plausível (`config.py`) vira nulo, não é
    descartado nem "consertado" — mesma filosofia de meses nublados: o site
    mostra "sem dado" em vez de um número inventado ou, pior, um número
    fisicamente impossível.

    Achado real ao rodar esta limpeza: 58 de 612.000 leituras de `lst_dia_c`
    (0,009%) vinham abaixo de 10°C — até -7,49°C, impossível pra superfície
    em Manaus. Concentradas em poucos meses específicos (2006-05, 2008-03,
    2007-03, entre outros) e com `lst_noite_c` nulo na mesma célula/mês —
    sinal de composição mensal formada por pouquíssimos pixels, um deles
    contaminado por nuvem que passou pelo QC de 03_lst_mensal.py (o QC ali
    aceita a flag "erro médio <= 2K", que não é uma garantia absoluta de
    céu limpo, só a garantia que existia disponível). Detalhes completos em
    `data/processed/criterios_limpeza.json`.
    """
    faixas = {
        "lst_dia_c": (LST_MIN_C, LST_MAX_C),
        "lst_noite_c": (LST_MIN_C, LST_MAX_C),
        "ndvi": (NDVI_MIN, NDVI_MAX),
    }

    for coluna, (minimo, maximo) in faixas.items():
        fora_da_faixa = ~tabela[coluna].between(minimo, maximo) & tabela[coluna].notna()
        n_fora = int(fora_da_faixa.sum())
        if n_fora:
            print(
                f"  {coluna}: {n_fora} valor(es) fora de [{minimo}, {maximo}] "
                "-> virando nulo"
            )
        tabela.loc[fora_da_faixa, coluna] = np.nan

    return tabela


def filtrar_inversao_termica(tabela: pd.DataFrame) -> pd.DataFrame:
    """
    Checagem extra, além da faixa plausível global (10-60°C): um valor como
    "11°C de dia" passa pela faixa acima (ela só rejeita abaixo de 10) mas
    ainda não faz sentido pra Manaus se, na mesma célula e mês, a noite
    registrou 25°C — mais quente que o dia por uma diferença grande demais
    pra ser clima (rever `LIMIAR_INVERSAO_NOITE_DIA_C` no config.py).

    Descoberta rodando contra os dados reais: 82 de 612.000 células-mês
    (0,013%) tinham essa inversão grande. Olhando as duas colunas separado
    dentro desse grupo, `lst_noite_c` continuava dentro da faixa normal da
    cidade (22-33°C, igual ao resto do dataset) mas `lst_dia_c` caía pra
    10-26°C, bem abaixo do normal — ou seja, é sempre a leitura diurna que
    está contaminada, nunca a noturna. Por isso só `lst_dia_c` vira nulo
    aqui, não as duas. Detalhes e números completos em
    `data/processed/criterios_limpeza.json`.
    """
    ambos_presentes = tabela["lst_dia_c"].notna() & tabela["lst_noite_c"].notna()
    inversao_grande = ambos_presentes & (
        tabela["lst_noite_c"] - tabela["lst_dia_c"] > LIMIAR_INVERSAO_NOITE_DIA_C
    )
    n_afetado = int(inversao_grande.sum())
    if n_afetado:
        print(
            f"  lst_dia_c: {n_afetado} valor(es) com noite mais quente que o dia "
            f"por mais de {LIMIAR_INVERSAO_NOITE_DIA_C}°C -> virando nulo"
        )
    tabela.loc[inversao_grande, "lst_dia_c"] = np.nan
    return tabela


def filtrar_anomalias_climatologicas(tabela: pd.DataFrame) -> pd.DataFrame:
    """
    Terceira checagem, além da faixa global e da inversão dia/noite: um
    valor pode estar dentro da faixa plausível E ter dia mais quente que
    noite, e ainda assim ser implausível *pra aquela célula específica*
    naquele mês do calendário — muito mais quente ou muito mais frio do que
    ela mesma costuma registrar em outros anos, no mesmo mês.

    Caso real que motivou este filtro: ~30 células vizinhas bateram
    38-42°C em junho/2001 (bem acima do que essas mesmas células registram
    em outros junhos). A julgar só pelo formato dos dados (pico concentrado,
    some no mês seguinte) parecia um evento real de calor — mas junho/2001
    teve recorde de FRIO documentado em Manaus, e o mesmo mês teve 0% de
    leitura noturna válida na grade inteira: o "pico" era sobra de poucos
    pixels de dia num mês excepcionalmente nublado, não um evento de calor
    de verdade. Ao contrário da inversão dia/noite (uma
    impossibilidade física clara), aqui o sinal de alarme é estatístico:
    `z` alto não prova erro, mas junto com uma completude de dado muito
    baixa naquele mês (visível na contagem de nulos), é forte evidência.

    `min_periods=10`: só calcula a média/desvio-padrão de uma célula-mês
    (ex.: "toda célula X em todo junho") se houver pelo menos 10 dos 25
    anos com dado — com menos que isso o desvio-padrão é instável demais
    pra confiar no `z`.
    """
    for coluna in COLUNAS_LST:
        grupo = tabela.groupby(["cell_id", "mes"])[coluna]
        media = grupo.transform("mean")
        contagem = grupo.transform("count")
        desvio = grupo.transform("std")

        z = (tabela[coluna] - media) / desvio
        anomalo = (
            tabela[coluna].notna() & (contagem >= 10) & (z.abs() > LIMIAR_Z_CLIMATOLOGICO)
        )
        n_anomalo = int(anomalo.sum())
        if n_anomalo:
            print(
                f"  {coluna}: {n_anomalo} valor(es) a mais de {LIMIAR_Z_CLIMATOLOGICO} "
                "desvios-padrão da própria média histórica (mesmo mês) -> virando nulo"
            )
        tabela.loc[anomalo, coluna] = np.nan

    return tabela


def checagens_de_sanidade(tabela: pd.DataFrame) -> None:
    for coluna, (minimo, maximo) in {
        "lst_dia_c": (LST_MIN_C, LST_MAX_C),
        "lst_noite_c": (LST_MIN_C, LST_MAX_C),
        "ndvi": (NDVI_MIN, NDVI_MAX),
    }.items():
        valores = tabela[coluna].dropna()
        assert valores.between(minimo, maximo).all(), (
            f"{coluna} ainda tem valor fora de [{minimo}, {maximo}] "
            "depois da limpeza — algo neste script não filtrou direito."
        )

    ambos_presentes = tabela["lst_dia_c"].notna() & tabela["lst_noite_c"].notna()
    ainda_invertido = ambos_presentes & (
        tabela["lst_noite_c"] - tabela["lst_dia_c"] > LIMIAR_INVERSAO_NOITE_DIA_C
    )
    assert not ainda_invertido.any(), (
        f"{int(ainda_invertido.sum())} célula(s)-mês ainda com noite > dia + "
        f"{LIMIAR_INVERSAO_NOITE_DIA_C}°C — filtrar_inversao_termica não pegou tudo."
    )

    print("Contagem de nulos por coluna (meses nublados / filtrados):")
    for coluna in COLUNAS_LST + [COLUNA_NDVI]:
        n_nulos = int(tabela[coluna].isna().sum())
        pct = 100 * n_nulos / len(tabela)
        print(f"  {coluna}: {n_nulos} ({pct:.1f}%)")


def salvar_parquets_por_ano(tabela: pd.DataFrame) -> None:
    """
    Parquet particionado por ano (não um arquivo único): o site só precisa
    carregar o(s) ano(s) visível(is) no slider a cada momento, não os 25
    anos inteiros de uma vez.
    """
    DIR_PROCESSED.mkdir(parents=True, exist_ok=True)
    colunas_finais = ["cell_id", "lon", "lat", "ano", "mes"] + COLUNAS_LST + [COLUNA_NDVI]

    total_salvo = 0
    for ano in range(ANO_INICIO, ANO_FIM + 1):
        fatia = tabela.loc[tabela["ano"] == ano, colunas_finais]
        caminho = DIR_PROCESSED / f"manaus_{ano}.parquet"
        fatia.to_parquet(caminho, index=False)
        total_salvo += len(fatia)

    assert total_salvo == len(tabela), (
        f"Soma das fatias por ano ({total_salvo}) difere do total ({len(tabela)})."
    )
    n_anos = ANO_FIM - ANO_INICIO + 1
    print(f"{n_anos} arquivos Parquet salvos em {DIR_PROCESSED} ({total_salvo} linhas no total).")


def _reprojetar_para_wgs84(celula: ee.Feature) -> ee.Feature:
    """
    `construir_grade()` desenha os retângulos em EPSG:3857 (Web Mercator,
    metros) — necessário pra "1000 m" ter sentido ao montar a grade (LST e
    NDVI). Mas o formato GeoJSON (RFC 7946) exige coordenadas em WGS84
    (EPSG:4326, graus de longitude/latitude); é o que o MapLibre GL (usado
    no site) espera ao ler um arquivo `.geojson`. Sem este passo, os
    polígonos sairiam com coordenadas como `-6702000` (metros) em vez de
    `-60.20` (graus) — carregariam sem erro, mas desenhariam a grade
    inteira fora do mapa, ou em escala absurda. `maxError=1` (1 metro) é a
    tolerância de aproximação aceita nessa reprojeção; irrelevante numa
    grade de 1 km.
    """
    geometria_wgs84 = celula.geometry().transform("EPSG:4326", 1)
    return celula.setGeometry(geometria_wgs84)


def gerar_grade_geojson(n_celulas_esperado: int) -> None:
    """
    Os CSVs só guardam o centroide de cada célula (`lon`, `lat`); o site
    precisa do polígono inteiro pra desenhar a grade no mapa.
    `construir_grade()` (mesma função usada nos scripts de LST e NDVI)
    recria essa geometria; `.getInfo()` traz o FeatureCollection inteiro
    pro Python já no formato GeoJSON padrão — viável aqui porque são só
    ~2.040 polígonos retangulares simples, bem abaixo do limite de payload
    de uma chamada direta (diferente das tabelas de 612 mil linhas, que
    precisaram do fluxo assíncrono de Export.table.toDrive nos scripts de
    LST e NDVI).
    """
    ee.Initialize(project=EE_PROJECT_ID)
    grade = (
        construir_grade()
        .select(["cell_id", "lon", "lat"])
        .map(_reprojetar_para_wgs84)
    )
    geojson = grade.getInfo()

    n_features = len(geojson["features"])
    assert n_features == n_celulas_esperado, (
        f"grade.geojson tem {n_features} células, esperava {n_celulas_esperado} "
        "(o número de células únicas encontrado nos CSVs de LST/NDVI)."
    )

    primeira_coordenada = geojson["features"][0]["geometry"]["coordinates"][0][0]
    lon0, lat0 = primeira_coordenada
    assert -60.5 < lon0 < -59.5 and -3.5 < lat0 < -2.5, (
        f"Coordenada {primeira_coordenada} fora do bbox de Manaus em graus — "
        "a reprojeção pra WGS84 não funcionou (ainda em metros?)."
    )

    caminho = DIR_PROCESSED / "grade.geojson"
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(geojson, arquivo, ensure_ascii=False)
    print(f"grade.geojson salvo em {caminho} ({n_features} células).")


def main() -> None:
    print("Lendo e juntando LST + NDVI...")
    tabela = carregar_e_juntar()

    print("Aplicando faixas plausíveis (config.py)...")
    tabela = aplicar_faixas_plausiveis(tabela)

    print("Filtrando inversão térmica implausível (noite muito mais quente que dia)...")
    tabela = filtrar_inversao_termica(tabela)

    print("Filtrando anomalias climatológicas (muito longe da própria média histórica)...")
    tabela = filtrar_anomalias_climatologicas(tabela)

    print("Checagens de sanidade...")
    checagens_de_sanidade(tabela)

    print("Salvando Parquet por ano...")
    salvar_parquets_por_ano(tabela)

    print("Gerando grade.geojson...")
    gerar_grade_geojson(n_celulas_esperado=tabela["cell_id"].nunique())

    print("Concluído.")


if __name__ == "__main__":
    main()
