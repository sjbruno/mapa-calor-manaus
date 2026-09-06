"""
Construção da grade espacial de análise.

Um único FeatureCollection de células retangulares de RESOLUCAO_M metros
cobrindo o bbox de Manaus (config.BBOX). Compartilhado entre os scripts de
LST (03), NDVI (04) e montagem final (05) para garantir que todos usem
exatamente a mesma grade e os mesmos cell_id — sem isso, o join por célula
entre temperatura e vegetação (a base de todo o cruzamento do projeto)
quebraria silenciosamente.
"""

import ee

from mapa_amazonia.config import BBOX, RESOLUCAO_M


def construir_grade() -> ee.FeatureCollection:
    """
    Cobre o bbox com uma grade regular de células de RESOLUCAO_M x
    RESOLUCAO_M metros, numa projeção métrica (Web Mercator, EPSG:3857 —
    necessária porque "1000 metros" só significa algo numa projeção que usa
    metro como unidade; graus de latitude/longitude não têm tamanho fixo).

    Cada célula ganha um cell_id determinístico, calculado a partir da
    posição do centro dela (não do system:index interno do Earth Engine,
    que é conveniente mas não é uma garantia documentada de estabilidade
    entre chamadas) — é isso que permite juntar (fazer join) a tabela de
    temperatura com a de vegetação depois, célula a célula.
    """
    regiao = ee.Geometry.Rectangle(BBOX)
    projecao = ee.Projection("EPSG:3857").atScale(RESOLUCAO_M)
    grade_bruta = regiao.coveringGrid(projecao)
    return grade_bruta.map(_nomear_celula)


def _nomear_celula(celula: ee.Feature) -> ee.Feature:
    centro = ee.Feature(celula).geometry().centroid(1)
    coordenadas = centro.coordinates()
    lon = coordenadas.get(0)
    lat = coordenadas.get(1)

    # "%.4f" arredonda pra 4 casas decimais (~11 m de precisão no equador) —
    # o suficiente pra dar um cell_id único e legível, já que células
    # vizinhas na grade de 1 km ficam a ~0.009 grau de distância uma da
    # outra. Não é uma coordenada pra uso geográfico de precisão.
    cell_id = (
        ee.String("c_")
        .cat(ee.Number(lon).format("%.4f"))
        .cat("_")
        .cat(ee.Number(lat).format("%.4f"))
    )
    return celula.set({"cell_id": cell_id, "lon": lon, "lat": lat})
