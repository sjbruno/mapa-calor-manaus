"""
Configuração central do projeto.

Por que este arquivo existe
---------------------------
Todo valor que aparece em mais de um script mora aqui e só aqui. Se um dia
decidirmos mudar o recorte do mapa ou o período analisado, mudamos numa linha
só e todos os scripts passam a usar o valor novo automaticamente.

O contrário disso — espalhar o número -60.20 por cinco arquivos — é como se
criam bugs em que metade do pipeline usa um recorte e a outra metade usa outro.

Como usar num script:

    from config import BBOX, ANO_INICIO, COLECAO_LST

Nada aqui executa nada. É só um conjunto de valores nomeados.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# 1. RECORTE ESPACIAL
# ---------------------------------------------------------------------------
# Bounding box ("caixa delimitadora"): um retângulo definido por dois cantos.
# Cobre a mancha urbana de Manaus + Rio Negro + Reserva Ducke + floresta ao
# norte. Incluir a floresta é proposital: é o contraste cidade/mata que dá
# sentido ao mapa.
#
# Longitude é o eixo leste-oeste; latitude, o norte-sul. Manaus fica no
# hemisfério sul e a oeste de Greenwich, então ambos são negativos.
#
# A ordem [oeste, sul, leste, norte] é a convenção que o Earth Engine espera
# em ee.Geometry.Rectangle().
BBOX = [-60.20, -3.20, -59.75, -2.85]

# Área resultante: ~50 km (leste-oeste) x ~39 km (norte-sul).
# Numa grade de 1 km isso dá aproximadamente 1.950 células.

# Resolução da grade de análise, em metros.
# 1000 m = resolução nativa do MOD11A2 (temperatura). O NDVI, que vem em 250 m,
# é agregado para cá — ver 04_ndvi_mensal.py.
RESOLUCAO_M = 1000

# Resolução nativa do MOD13Q1 (NDVI) — usada como `scale` no reduceRegions de
# 04_ndvi_mensal.py, pra agregação 250 m -> grade de 1 km ser feita na
# resolução certa.
RESOLUCAO_NDVI_NATIVA_M = 250

# ---------------------------------------------------------------------------
# 2. RECORTE TEMPORAL
# ---------------------------------------------------------------------------
# MODIS começa em 18/02/2000, ou seja, 2000 é um ano incompleto e estragaria
# qualquer comparação anual. E as coleções morrem no meio de 2026 (fim da missão
# Terra/Aqua). Ficamos com 25 anos civis completos.
ANO_INICIO = 2001
ANO_FIM = 2025

# ---------------------------------------------------------------------------
# 3. COLEÇÕES DO EARTH ENGINE
# ---------------------------------------------------------------------------
# Temperatura de superfície (LST — Land Surface Temperature).
# Composição de 8 dias, 1 km, já com máscara de nuvem embutida.
# Cobertura: 18/02/2000 até 13/08/2026 (fim da missão).
COLECAO_LST = "MODIS/061/MOD11A2"

# Índice de vegetação (NDVI).
# Composição de 16 dias, 250 m, também já cloud-masked.
# Cobertura: 18/02/2000 até 28/07/2026.
COLECAO_NDVI = "MODIS/061/MOD13Q1"

# Ocorrência histórica de água — usada para mascarar o Rio Negro.
# Sem isso o rio (NDVI negativo) seria lido como "área degradada". Ver 04_ndvi_mensal.py.
COLECAO_AGUA = "JRC/GSW1_4/GlobalSurfaceWater"
# Banda "occurrence": % das vezes em que aquele pixel foi água entre 1984 e 2021.
# 100 = sempre água (leito do rio); 0 = nunca.
BANDA_AGUA = "occurrence"

# Limiar decidido olhando a distribuição real de occurrence no bbox:
# o histograma é fortemente bimodal — a grande maioria dos pixels com QUALQUER
# valor de occurrence está entre 90-100 (leito permanente do rio), com uma
# cauda pequena de pixels "molhados às vezes" nas faixas mais baixas. 50 separa
# bem "normalmente água" de "terra que ocasionalmente alaga" — mascaramos
# como água tudo que apareceu molhado em pelo menos metade dos anos observados.
LIMIAR_OCCURRENCE_AGUA = 50

# ---------------------------------------------------------------------------
# 4. FATORES DE ESCALA
# ---------------------------------------------------------------------------
# Satélites guardam números inteiros para economizar espaço. Para chegar ao
# valor físico é preciso multiplicar pelo fator de escala.
#
# Errar isto é O erro clássico do projeto. Se sua temperatura der 6000, você
# esqueceu o fator. Se der 300, esqueceu de subtrair o zero absoluto.

# LST vem em Kelvin multiplicado por 50 (ou seja, escala 0.02).
ESCALA_LST = 0.02
# Kelvin -> Celsius: subtrair 273.15.
ZERO_ABSOLUTO = 273.15

# NDVI vem multiplicado por 10.000. Então 8000 no arquivo significa 0.8.
ESCALA_NDVI = 0.0001

# ---------------------------------------------------------------------------
# 5. CAMINHOS
# ---------------------------------------------------------------------------
# Path(__file__) é o caminho deste arquivo. Este arquivo mora em
# src/mapa_amazonia/config.py, então a raiz do projeto (onde ficam data/ e
# site/) fica duas pastas acima: config.py -> mapa_amazonia/ -> src/ -> raiz.
# .resolve() garante caminho absoluto, não importa de qual pasta o script foi
# chamado no terminal — uma das causas mais comuns de "FileNotFoundError"
# para quem está começando.
RAIZ = Path(__file__).resolve().parents[2]
DIR_RAW = RAIZ / "data" / "raw"
DIR_PROCESSED = RAIZ / "data" / "processed"
DIR_SITE = RAIZ / "site"

# ---------------------------------------------------------------------------
# 6. PONTOS DE REFERÊNCIA PARA VALIDAÇÃO
# ---------------------------------------------------------------------------
# Coordenadas (latitude, longitude) usadas para checar se o pipeline
# reproduz padrões que a literatura já descreveu (validação em
# 04_ndvi_mensal.py).
#
# ATENÇÃO: estas coordenadas são APROXIMADAS — centroides estimados, não
# oficiais. Antes de usá-las como prova de qualquer coisa, elas precisam
# ser conferidas num mapa. Estão aqui como ponto de partida.
PONTOS_REFERENCIA = {
    # Deve ser o mais FRIO e mais VERDE — floresta preservada.
    "reserva_ducke": (-2.960, -59.930),
    # Deve ser o mais QUENTE — adensamento e pouca árvore.
    "centro": (-3.130, -60.023),
    # Citados no estudo da UEA (2002-2012) como picos de ilha de calor.
    "aleixo": (-3.093, -59.985),
    "petropolis": (-3.115, -59.985),
    "cidade_nova": (-3.020, -60.000),
    "japiim": (-3.108, -59.997),
    # Controle: área urbana mas arborizada e perto do rio.
    "ponta_negra": (-3.070, -60.090),
}

# ---------------------------------------------------------------------------
# 7. FAIXAS PLAUSÍVEIS (usadas nas checagens de sanidade de 05_montar_tabelas.py)
# ---------------------------------------------------------------------------
# Qualquer valor fora destas faixas indica erro de processamento, não um dado
# interessante. Manaus não faz 5 °C nem 80 °C de superfície.
LST_MIN_C, LST_MAX_C = 10.0, 60.0
NDVI_MIN, NDVI_MAX = -1.0, 1.0

# Checagem adicional, específica de Manaus (não é uma faixa absoluta como as
# de cima): a superfície à noite não deveria ficar mais de
# LIMIAR_INVERSAO_NOITE_DIA_C graus mais quente que de dia, na mesma célula
# e mês. Cidade equatorial, sol forte o ano todo — o normal é o dia ser mais
# quente (mediana histórica: +5,6 °C). Uma inversão pequena (1-3 °C) é
# plausível num mês de chuva muito pesada (o dia fica encoberto o mês
# inteiro); acima de 5 °C, olhando a distribuição real dos dados,
# é sempre a leitura diurna que está fora do normal, nunca a noturna —
# resíduo de nuvem que passou pelo QC, não um evento climático.
LIMIAR_INVERSAO_NOITE_DIA_C = 5.0

# Segunda checagem específica de Manaus: um valor de LST muito distante da
# própria média histórica daquela célula NO MESMO MÊS DO CALENDÁRIO (ex.:
# todos os junhos de uma célula, não o ano inteiro — evita confundir a
# sazonalidade real da cidade com anomalia) é suspeito, esteja ele muito
# frio OU muito quente. Um caso real motivou este limiar: um grupo de
# ~30 células vizinhas bateu 38-42°C em junho/2001 — a princípio parecia
# um evento real (queimada), mas junho/2001 teve recorde de FRIO em Manaus
# (fonte externa, não satélite) e o mês tinha 0% de leitura noturna válida
# na grade inteira — ou seja, o pico "quente" veio de pouquíssimos pixels
# de dia sobrando num mês excepcionalmente nublado, não de um evento real.
# 4 desvios-padrão da própria média histórica da célula naquele mês.
LIMIAR_Z_CLIMATOLOGICO = 4.0

# ---------------------------------------------------------------------------
# 8. EARTH ENGINE — SEU PROJETO
# ---------------------------------------------------------------------------
# Preencha depois de criar o projeto no Google Cloud e registrá-lo como
# noncommercial. É uma string tipo "ee-seunome" ou "meu-projeto-123456".
EE_PROJECT_ID = "mapa-amazonia"
