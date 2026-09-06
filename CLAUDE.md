# Projeto: Temperatura Histórica x Áreas Verdes — Manaus

## Propósito

Site que mostra o histórico de temperatura de Manaus cruzado espacialmente com a
cobertura vegetal / áreas verdes da cidade, com evolução planejada para cruzar
também com o desenvolvimento urbano (infraestrutura nova e notícias sobre obras).
O objetivo central é visualizar como a perda de vegetação urbana se relaciona com
o aumento de temperatura ao longo do tempo e do espaço em Manaus.

Este documento consolida o que já foi pesquisado e decidido numa conversa de
planejamento anterior. A ideia é que a partir daqui um projeto no Claude Code
aprofunde o planejamento de implementação (arquitetura de dados, pipeline,
front-end) — este arquivo é o brief de contexto, não o plano de implementação.

## Decisões de escopo já tomadas

- **Sem recorte por bairro.** Não existe malha oficial e padronizada de bairros no
  Brasil (o IBGE só tem setores censitários, que às vezes não coincidem com os
  bairros "de fato"). Em vez disso, o projeto usa uma **grade espaço-temporal
  contínua** (raster de células, ex: 250m–1km) sobre a área de Manaus como unidade
  básica de análise.
- **Cadência mensal e anual**, não diária. Não há mudanças relevantes de vegetação
  de um dia para o outro, e a própria cadência de revisita dos satélites e a
  nebulosidade da Amazônia já empurram o projeto para essa granularidade.
- A camada de vegetação mensal precisa vir de **NDVI calculado direto da imagem de
  satélite** — o MapBiomas (mapa classificado) é anual "de fábrica" e não tem
  versão mensal, então vira uma camada complementar/de validação anual, não a
  fonte principal do "verde" mês a mês.

## Camadas de dados

### 1. Temperatura (mensal + anual)

Fonte primária recomendada: **MODIS**, via Google Earth Engine
- `MOD11A2` — Temperatura de Superfície (LST), composição de 8 dias, 1km de
  resolução, já com máscara de nuvem embutida. Agregar os composites de 8 dias que
  caem dentro de cada mês para gerar a média mensal; a média anual é derivada das
  12 médias mensais (ou só dos meses de seca, se quiser um valor mais comparável
  ano a ano).
- Trade-off vs. Landsat: perde resolução espacial (1km vs. 30–100m) e histórico
  anterior a 2000, mas ganha muito em robustez de pipeline (não precisa montar
  máscara de nuvem manualmente).

Alternativa de maior resolução: **Landsat 5/7/8/9** (bandas termais), via Earth
Engine — 30–100m, mas revisita de 16 dias e nebulosidade constante na Amazônia
tornam a composição mensal mais trabalhosa (alguns meses podem sobrar com poucos
pixels bons). Histórico desde 1984.

Complemento de série temporal densa e sem lacunas: **Open-Meteo** (reanálise
ERA5) — API gratuita, sem autenticação, dados horários/diários desde 1940. É um
ponto único (não granular espacialmente), mas serve como "termômetro geral da
cidade" para contextualizar e validar as camadas de satélite.

### 2. Vegetação / área verde (mensal + anual)

Fonte primária recomendada: **MODIS**, via Google Earth Engine
- `MOD13Q1` — Índice de vegetação (NDVI/EVI), composição de 16 dias, 250m de
  resolução, já cloud-masked. Agregar os composites de 16 dias que caem dentro de
  cada mês.

Alternativa de maior resolução: NDVI calculado manualmente a partir de bandas do
Landsat (mesmas ressalvas de nuvem/revisita do item acima) ou do Sentinel-2 (10m,
revisita de 5 dias, mas histórico só a partir de 2015).

Camada anual complementar/de validação: **MapBiomas** — mapas de uso e cobertura
do solo já classificados (floresta, área urbana, água etc.), anuais desde 1985,
disponíveis como asset direto no Google Earth Engine
(`projects/mapbiomas-public/assets/...`), sem custo. Não usar como fonte de
cadência mensal.

### 3. Infraestrutura urbana (fase 2)

- O próprio MapBiomas já classifica "área urbanizada" ano a ano — dá o avanço do
  concreto sem precisar raspar notícia.
- Malha viária/edificações específicas: histórico de edições do **OpenStreetMap**
  (via Overpass API ou dumps de histórico completo; `osmnx` em Python) — proxy
  razoável de quando uma via ou construção passou a existir no mapa (não
  necessariamente a data real da obra).

### 4. Notícias geolocalizadas (fase 3)

- **GDELT Project** — banco de eventos noticiosos geocodificados, gratuito,
  histórico desde 1979, acesso via Google BigQuery.
- Ressalva: a geocodificação é a nível de cidade, e a cobertura de veículos locais
  de Manaus (A Crítica, Portal Amazônia, G1 AM) tende a ser esparsa comparada a
  grandes veículos internacionais. Provavelmente vai precisar complementar com
  scraping direto desses veículos + um passo de NLP para extrair a região/rua
  citada em cada notícia.

## Contexto local já levantado (Manaus)

- Estudo da UEA (2002–2012) mapeou picos de ilha de calor concentrados na zona
  centro-sul e sul, em bairros como Aleixo e Petrópolis, além de Cidade Nova,
  Tancredo Neves, Zumbi e Japiim — bom ponto de partida para validar se o pipeline
  reproduz um padrão já conhecido.
- Reportagem da InfoAmazonia (com dados de satélite) mediu diferenças de até 10°C
  entre ilhas de calor e áreas de floresta preservada nas proximidades; mais de
  85% da população de Manaus vive em bairros com temperatura de superfície pelo
  menos 3°C acima da área preservada.
- Segundo o MapBiomas/Inpa, Manaus é a capital que mais perdeu vegetação urbana
  nos últimos 20 anos; o Censo IBGE 2022 registra a taxa de arborização de vias
  públicas da cidade em apenas 44,81%.
- O grupo de pesquisa "Árvores do Asfalto" (UFAM) é ativo no tema — possível fonte
  ou contato para validação ou dados adicionais.

## Obstáculos técnicos conhecidos

- **Nebulosidade amazônica**: reduz drasticamente a quantidade de imagens
  ópticas/termais utilizáveis por mês. É o principal motivo para preferir
  composites já prontos (MODIS 8/16 dias) em vez de montar composição manual a
  partir de imagens brutas do Landsat.
- **Ausência de malha oficial de bairros**: motivou a decisão de trabalhar com
  grade espaço-temporal em vez de polígonos administrativos.
- **MapBiomas é anual, não mensal**: não serve como fonte de cadência mensal, só
  como camada de contexto/validação.
- **Trade-off resolução x robustez de pipeline**: MODIS (1km–250m, pipeline
  simples) vs. Landsat (30–100m, pipeline mais trabalhoso) — decisão de qual usar
  (ou os dois, em camadas separadas) ainda em aberto para o planejamento de
  implementação.
- **GDELT geocodifica a nível de cidade**: não é granular o suficiente sozinho
  para localizar notícias por rua/região dentro de Manaus; precisa de
  enriquecimento (NLP + fontes locais).

## Direção geral de stack técnico (não fechada)

- **Coleta/processamento**: Python, `earthengine-api` / `geemap` (MODIS + Landsat
  + MapBiomas via Google Earth Engine), `osmnx` / `geopandas` (malha viária).
  Pipeline roda periodicamente (não em tempo real) e salva resultados agregados
  (GeoJSON / Parquet / tiles) — não é viável servir raster bruto direto para o
  navegador.
- **Front-end**: mapa interativo (Leaflet ou Mapbox GL) com camadas togglable
  (temperatura, vegetação, infraestrutura, eventos) e slider de tempo
  (mês/ano).
- O autor está aprendendo Python através de projetos práticos — vale manter o
  código didático/comentado onde fizer sentido.

## Perguntas em aberto para o planejamento de implementação

- MODIS puro é suficiente, ou vale complementar com Landsat em pontos específicos
  para ganhar resolução?
- Qual o tamanho de célula da grade (250m? 500m? 1km?) — depende do equilíbrio
  entre nível de detalhe desejado e resolução real dos dados de satélite
  escolhidos.
- Usar toda a série histórica disponível (Landsat desde 1984) ou focar no período
  coberto pelo MODIS (desde 2000), que tem pipeline mais simples?
- Estrutura de armazenamento para os dados agregados (arquivo estático vs. banco
  de dados) e onde hospedar o site.
- Escopo exato da fase 2 (infraestrutura urbana) e fase 3 (notícias) — ainda não
  detalhado a nível de implementação.
