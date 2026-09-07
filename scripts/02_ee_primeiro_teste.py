"""
Earth Engine: menor exemplo possível de um cálculo completo.

Imprime a temperatura de superfície média de Manaus em julho de 2020, com o
cálculo mais simples possível — só pra deixar explícito um conceito central
do Earth Engine: ele não processa nada na máquina local. `ee.ImageCollection`,
`ee.Image`, `ee.Geometry` e `ee.Number` são *descrições* de um cálculo, não o
resultado em si. O cálculo de verdade só acontece no servidor do Google
quando `.getInfo()` é chamado (ou um Export é feito) — é aí que a descrição
vira número.
"""

import ee

from mapa_amazonia.config import (
    BBOX,
    COLECAO_LST,
    EE_PROJECT_ID,
    ESCALA_LST,
    RESOLUCAO_M,
    ZERO_ABSOLUTO,
)


def inicializar() -> None:
    """
    Autentica (lê a credencial salva em ~/.config/earthengine/credentials,
    gerada por `earthengine authenticate`) e associa as chamadas seguintes
    ao Project ID configurado.
    """
    ee.Initialize(project=EE_PROJECT_ID)


def montar_regiao() -> ee.Geometry:
    """
    BBOX está em [oeste, sul, leste, norte] (ver config.py) — exatamente a
    ordem que ee.Geometry.Rectangle espera. Isto ainda não busca nem toca
    em nenhum dado: é só a descrição de um retângulo, que o servidor só vai
    usar de verdade quando entrar num reduceRegion ou filterBounds.
    """
    return ee.Geometry.Rectangle(BBOX)


def temperatura_media_julho_2020(regiao: ee.Geometry) -> float:
    """
    Três passos, cada um uma operação "server-side" (ainda sem número
    nenhum na sua máquina):

    1. Filtra a coleção MOD11A2 (composições de 8 dias) para as que caem
       dentro de julho de 2020 e tocam a região; seleciona só a banda de
       temperatura diurna.
    2. `.mean()` colapsa a coleção (várias imagens de 8 dias) numa imagem
       só, com a média pixel a pixel ao longo do tempo.
    3. `.reduceRegion(...)` colapsa essa imagem numa média espacial única
       (todos os pixels dentro do bbox viram um número).

    Só o `.getInfo()` final força o servidor a computar tudo isso e mandar
    o resultado de volta — antes dele, `colecao`, `imagem_media` e
    `resultado` são só descrições.
    """
    colecao = (
        ee.ImageCollection(COLECAO_LST)
        .filterDate("2020-07-01", "2020-08-01")
        .filterBounds(regiao)
        .select("LST_Day_1km")
    )

    imagem_media = colecao.mean()

    resultado = imagem_media.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=regiao,
        scale=RESOLUCAO_M,
    )

    # .get("LST_Day_1km") ainda é uma descrição (um ee.ComputedObject).
    # .getInfo() é a linha que efetivamente comunica com o servidor.
    valor_bruto = resultado.get("LST_Day_1km").getInfo()

    # Fator de escala do MOD11A2: Kelvin x 50 (escala 0.02), depois
    # Kelvin -> Celsius subtraindo o zero absoluto. Ver config.py, seção 4 —
    # "o erro clássico do projeto" é esquecer um desses dois passos.
    return valor_bruto * ESCALA_LST - ZERO_ABSOLUTO


def main() -> None:
    inicializar()
    regiao = montar_regiao()
    temperatura_c = temperatura_media_julho_2020(regiao)
    print(f"Temperatura média de superfície em Manaus, julho/2020: {temperatura_c:.2f} °C")


if __name__ == "__main__":
    main()
