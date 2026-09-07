# Instruções para edição — humano ou agente de IA

Este documento explica como este repositório é organizado, como rodar o
pipeline de dados, como editar o site e como o deploy funciona. Não é um
tutorial de conceitos gerais (Python, Git, Earth Engine) — é um mapa direto
de "onde mexer pra fazer o quê".

## Estrutura do repositório

```
├── site/                    # Site estático (HTML/CSS/JS puro, sem build)
│   └── index.html           # Página única — é isto que o Vercel publica
├── scripts/                 # Pipeline de dados, roda em ordem (01 a 08)
├── src/mapa_amazonia/       # Código compartilhado entre os scripts
│   ├── config.py            # Todo parâmetro do projeto mora aqui
│   ├── grade.py             # Construção da grade espacial (Earth Engine)
│   └── drive.py             # Download das exportações do Earth Engine
├── data/
│   ├── raw/                 # CSVs baixados do Earth Engine (não versionado)
│   └── processed/           # Parquet + JSON finais (versionado — o site lê daqui)
├── pyproject.toml           # Dependências (gerenciadas com uv)
└── README.md                # Visão geral do projeto + metodologia completa
```

O repositório contém duas coisas que não têm relação de build entre si: o
pipeline Python que gera os dados, e o site estático que os lê. O Vercel só
enxerga `site/` (ver seção "Deploy" abaixo).

## Rodando o pipeline de dados

Pré-requisitos: Python 3.12+, [`uv`](https://docs.astral.sh/uv/), uma conta
Google Cloud com um projeto Earth Engine registrado (gratuito, categoria
noncommercial).

```bash
uv sync                          # instala as dependências
earthengine authenticate         # autentica sua conta (uma vez só)
```

Preencha `EE_PROJECT_ID` em `src/mapa_amazonia/config.py` com o ID do seu
projeto Earth Engine. Depois rode os scripts em ordem, de dentro de `scripts/`:

| Script | O que faz |
|---|---|
| `01_temperatura_ar.py` | Baixa a série histórica de temperatura do ar (Open-Meteo), 1940–hoje |
| `02_ee_primeiro_teste.py` | Checagem isolada: um número só, valida a conta do Earth Engine |
| `03_lst_mensal.py` | Exporta temperatura de superfície (LST) mensal por célula da grade |
| `04_ndvi_mensal.py` | Exporta NDVI (vegetação) mensal por célula da grade |
| `05_montar_tabelas.py` | Junta LST + NDVI, aplica os critérios de limpeza, salva Parquet por ano |
| `06_deriva_orbital.py` | Mede o horário real de passagem do satélite Terra por mês |
| `07_curva_horaria_ar.py` | Calcula a curva horária real de temperatura do ar (calibração) |
| `08_corrigir_deriva_orbital.py` | Aplica a correção de deriva orbital, gera `*_corrigido` |

Os scripts 03 e 04 exportam para o Google Drive de forma assíncrona (Earth
Engine não permite exportar tabelas grandes de forma síncrona) — baixe os
CSVs resultantes para `data/raw/` antes de rodar `05_montar_tabelas.py`.

A metodologia completa de cada etapa de limpeza — o quê, o porquê, quantos
valores afetou — está documentada em `data/processed/criterios_limpeza.json`
e resumida no README (seção "Metodologia").

## Adaptando para outra cidade

O pipeline não tem nada hardcoded específico de Manaus dentro da lógica —
os parâmetros que mudam ficam todos em `src/mapa_amazonia/config.py`:

- `BBOX`: retângulo `[oeste, sul, leste, norte]` da área de análise.
- `PONTOS_REFERENCIA`: coordenadas usadas para validar o pipeline contra
  padrões já conhecidos (ex.: "essa área deveria dar mais quente que aquela").
- `ANO_INICIO` / `ANO_FIM`: recorte temporal.
- `RESOLUCAO_M`: tamanho da célula da grade, em metros.

Dois limiares foram calibrados olhando a distribuição real dos dados de
Manaus e podem precisar reavaliação em outra região:
`LIMIAR_OCCURRENCE_AGUA` (máscara de água) e `LIMIAR_Z_CLIMATOLOGICO`
(filtro de anomalia climatológica). Veja os comentários ao lado de cada um
em `config.py` para o raciocínio usado para chegar no valor.

A correção de deriva orbital (scripts 06–08) é específica do satélite Terra
(MOD11A2) e da janela 2020–2026 em que a deriva está documentada pela NASA —
revise se ainda se aplica antes de reusar em um projeto com período diferente.

## Editando o site

`site/index.html` é um arquivo único, sem build step: HTML, CSS e JS estão
todos ali, sem framework, sem bundler. Os dados (grade de 2.040 células por
25 anos, série de dispersão, série do hotspot) estão embutidos no próprio
HTML como JSON — não há chamada de API em tempo de execução.

Para atualizar os números depois de rodar o pipeline de novo: os dados que
alimentam o site vêm de `data/processed/` (os Parquet por ano, `grade.geojson`
e os JSONs de contexto). Não existe hoje um script automático que regenera o
HTML embutido a partir desses arquivos — a atualização é manual, editando os
blocos de dados diretamente no `<script>` do `index.html`.

Para rodar localmente, basta abrir `site/index.html` num navegador (ou servir
a pasta `site/` com qualquer servidor estático — `python3 -m http.server`,
por exemplo).

## Deploy (Vercel)

O site é 100% estático e não precisa de variável de ambiente nem de função
serverless. Ao criar o projeto no Vercel:

1. Conecte este repositório do GitHub.
2. Em **Project Settings → General → Root Directory**, aponte para `site/`.
3. Framework preset: **Other** (sem build command, sem output directory —
   é HTML estático puro).

O restante do repositório (`scripts/`, `src/`, `data/`) fica fora do que o
Vercel enxerga, porque o Root Directory restringe o build a `site/`. Não é
necessário nem recomendado manter dois repositórios separados: um repo só,
com Root Directory apontando para a pasta certa, resolve o fato de o repo
ter conteúdo (o pipeline Python) que não faz sentido nenhum pro Vercel.

Antes de tornar o repositório público, audite por segredo ou caminho local
exposto: nenhuma credencial do Earth Engine/Drive deve estar versionada
(`.gitignore` já cobre isso), e `EE_PROJECT_ID` em `config.py` é um ID de
projeto Google Cloud, não uma credencial — pode ficar público, mas revise
mesmo assim antes de publicar.
