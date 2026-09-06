# Estudo — Mapa Amazônia

Este arquivo é o material paralelo do projeto. A cada bloco pequeno que eu
implemento, escrevo aqui: o que foi feito, por que dessa forma e não de outra,
e o que dá pra aprender ali. É pra você ler *depois*, sem precisar ter
acompanhado a execução — cada seção é autocontida.

Ordem: mais recente no topo? Não — cronológica, de cima pra baixo, porque o
projeto é cumulativo (cada fase depende de conceitos da anterior).

## Índice

<!-- Atualizar esta lista toda vez que uma seção nova (### ou ##) for
adicionada ao arquivo. Os links são âncoras de melhor esforço — a maioria
dos visualizadores markdown (VS Code, GitHub) as reconhece, mas se algum
link não pular direto, a seção ainda está logo abaixo na ordem do índice. -->

- [Fase 0 — Ambiente](#fase-0-ambiente)
  - [O que foi feito](#o-que-foi-feito)
  - [O que é `uv`](#o-que-é-uv)
  - [O que `uv init --bare ... --vcs none` fez](#o-que-uv-init---bare--vcs-none-fez)
  - [O que é `pyproject.toml`](#o-que-é-pyprojecttoml)
  - [Por que essas 5 bibliotecas e não outras](#por-que-essas-5-bibliotecas-e-não-outras)
  - [O que `git init` fez](#o-que-git-init-fez)
  - [Estado do projeto ao final da Fase 0](#estado-do-projeto-ao-final-da-fase-0-antes-do-adendo-abaixo)
  - [Adendo — de `config.py` solto pra pacote instalável](#adendo-05092026--de-configpy-solto-pra-pacote-instalável)
- [Fase 1 — Primeira série temporal real (Open-Meteo)](#fase-1--primeira-série-temporal-real-open-meteo)
  - [Objetivo desta fase](#objetivo-desta-fase)
  - [Antes dos blocos: `nome: Tipo` e `-> Tipo`](#antes-dos-blocos-a-sintaxe-nome-tipo-e---tipo)
  - [O que é a Open-Meteo Archive API](#o-que-é-a-open-meteo-archive-api)
  - [Bloco 1 — `buscar_dados_diarios()`](#bloco-1--buscar_dados_diarios)
  - [Bloco 2 — `montar_dataframe()`](#bloco-2--montar_dataframe-por-que-o-json-é-colunar)
  - [Bloco 3 — `atualizar_serie()`: busca incremental](#bloco-3--atualizar_serie-busca-incremental)
  - [Bloco 4 — `agregar_mensal_e_anual()`: o `resample`](#bloco-4--agregar_mensal_e_anual-o-resample)
  - [Bloco 5 — salvar só o diário](#bloco-5--salvar-só-o-diário-não-o-mensalanual)
  - [A armadilha do `import`](#a-armadilha-do-import)
  - [Resultado](#resultado)
- [Fase 2 — Earth Engine: conta e o primeiro número](#fase-2--earth-engine-conta-e-o-primeiro-número)
  - [Objetivo desta fase](#objetivo-desta-fase-1)
  - [O conceito central: client vs. server](#o-conceito-central-client-vs-server)
  - [Bloco 1 — `inicializar()`](#bloco-1--inicializar)
  - [Bloco 2 — `montar_regiao()`](#bloco-2--montar_regiao)
  - [Bloco 3 — `temperatura_media_julho_2020()`](#bloco-3--temperatura_media_julho_2020-os-três-passos-server-side)
  - [Armadilha: certificado SSL](#armadilha-real-de-sistema-não-do-earth-engine-certificado-ssl)
  - [Resultado](#resultado-1)
- [Fase 3 — Temperatura mensal, 2001-2025](#fase-3--temperatura-mensal-2001-2025)
  - [Objetivo desta fase](#objetivo-desta-fase-2)
  - [Por que um módulo `grade.py` separado](#por-que-um-módulo-gradepy-separado-em-vez-de-código-dentro-do-script)
  - [`construir_grade()`](#construir_grade-cobrindo-o-bbox-com-células-de-1-km)
  - [A máscara de qualidade (QC)](#a-máscara-de-qualidade-qc--bits-dentro-de-um-número)
  - [De 8 em 8 dias pra média mensal](#de-8-em-8-dias-pra-média-mensal-sem-loop-python)
  - [De imagem mensal pra tabela por célula](#de-imagem-mensal-pra-tabela-por-célula)
  - [`ee.List.sequence` + `.map()` pros 300 meses](#sem-loop-python-pros-300-meses-eelistsequence--map)
  - [Validação antes de gastar cota](#validação-antes-de-gastar-cota-validar_contra_fase_2)
  - [Exportação assíncrona](#exportação-assíncrona-por-que-o-script-não-termina-na-hora)
  - [Primeira exportação (com bug)](#primeira-exportação-com-bug-corrigido-logo-abaixo)
  - [Baixando do Drive: `drive.py`](#baixando-do-drive-automaticamente-srcmapa_amazoniadrivepy)
  - [Armadilha: `LST_Night_1km` vazio](#armadilha-real-lst_night_1km-saiu-100-vazio)
  - [Resultado (depois da correção)](#resultado-depois-da-correção)
- [Fase 4 — NDVI mensal, na mesma grade](#fase-4--ndvi-mensal-na-mesma-grade)
  - [Objetivo desta fase](#objetivo-desta-fase-3)
  - [O que é NDVI](#o-que-é-ndvi)
  - [`SummaryQA` do MOD13Q1](#summaryqa-do-mod13q1-mais-simples-que-o-qc-bit-a-bit-da-fase-3)
  - [A máscara de água: `.unmask(0)`](#a-máscara-de-água-por-que-precisa-de-unmask0)
  - [Escolhendo o limiar de 50](#escolhendo-o-limiar-de-50-olhando-a-distribuição-real-não-chutando)
  - [Armadilha: nome da coluna do `reduceRegions`](#armadilha-real-reduceregions-nomeia-a-coluna-diferente-pra-1-banda-vs-várias)
  - [Validação contra os pontos de referência](#validação-contra-os-pontos-de-referência)
  - [Resultado](#resultado-3)

---

## Fase 0 — Ambiente

### O que foi feito

Três comandos, nessa ordem:

```bash
uv init --bare --python 3.12 --name mapa-amazonia --vcs none
uv add earthengine-api pandas requests pyarrow matplotlib
git init
```

Resultado: um `pyproject.toml`, um `.venv/` (não versionado), um `uv.lock`, e
um repositório git vazio, criados na raiz do projeto.

### O que é `uv`

`uv` é um gerenciador de projetos Python — resolve versões de dependências,
cria e gerencia o ambiente virtual, e roda os scripts dentro dele. É um
substituto mais rápido e mais simples de `pip` + `venv` + `virtualenv` juntos.

**Por que ambiente virtual existe.** Cada projeto Python normalmente precisa
de versões diferentes de bibliotecas. Se você instalasse tudo "no sistema"
(`pip install pandas` direto), dois projetos que precisam de versões
diferentes de `pandas` entrariam em conflito — instalar um quebraria o outro.
O ambiente virtual (`.venv/`) é uma cópia isolada do Python só para este
projeto, com só as bibliotecas que ele declarou.

### O que `uv init --bare ... --vcs none` fez

- `--bare`: cria só o `pyproject.toml`, sem gerar um `main.py` de exemplo nem
  um `README.md` — o projeto já tinha estrutura própria (`scripts/`, `data/`,
  `CLAUDE.md`), não precisávamos do template padrão.
- `--python 3.12`: fixa a versão do Python que este projeto usa. Isso importa
  porque o `earthengine-api` e outras libs de geoprocessamento às vezes
  demoram a suportar a versão mais nova do Python (aqui, sua máquina tem
  Python 3.14 instalado globalmente, mas o projeto pode pedir 3.12 e o `uv`
  baixa esse Python especificamente para o `.venv/` — repare no log:
  "Using CPython 3.14.6 interpreter" foi só pra *criar* o ambiente; o
  `pyproject.toml` registra `requires-python = ">=3.12"`, uma faixa mínima,
  não uma versão travada).
- `--vcs none`: não inicializa git sozinho — fizemos isso manualmente depois,
  por clareza (ver abaixo).

### O que é `pyproject.toml`

É o arquivo padrão da comunidade Python (não é invenção do `uv`) que declara
metadados do projeto e suas dependências. Ele é o que faz `uv add pandas`
"lembrar" que este projeto precisa de pandas, para que qualquer pessoa (ou
você, num computador novo) rode `uv sync` e reconstrua o ambiente idêntico —
sem isso, dependência vira "funciona na minha máquina".

Conteúdo gerado, com as 5 dependências que a Fase 0 do plano pedia:

```toml
[project]
name = "mapa-amazonia"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "earthengine-api>=1.7.42",
    "matplotlib>=3.11.1",
    "pandas>=3.0.5",
    "pyarrow>=25.0.1",
    "requests>=2.34.2",
]
```

### Por que essas 5 bibliotecas e não outras

- **`earthengine-api`**: o cliente Python do Google Earth Engine — usado a
  partir da Fase 2 para pedir os dados de satélite.
- **`pandas`**: manipulação de tabelas (o resultado do Earth Engine e do
  Open-Meteo vira uma tabela — linhas = célula×mês, colunas = temperatura,
  NDVI etc.).
- **`requests`**: para chamar a API do Open-Meteo (Fase 1) — uma chamada HTTP
  simples, sem autenticação.
- **`pyarrow`**: é o motor que o pandas usa por baixo para ler/escrever
  arquivos `.parquet` — o formato de armazenamento final decidido no plano
  (mais compacto e mais rápido de ler que `.csv`, e guarda o tipo de cada
  coluna, o que `.csv` não faz).
- **`matplotlib`**: só para gráficos de conferência durante o desenvolvimento
  (ex.: "esse mês de temperatura faz sentido visualmente?") — não é usado no
  site final (isso é MapLibre, no navegador).

Repare que **não instalamos** `rasterio`, `gdal` ou `geopandas` — de propósito
(ver CLAUDE.md / plano: o processamento pesado de raster roda nos servidores
do Earth Engine, não na sua máquina, então essas libs pesadas e difíceis de
compilar não são necessárias na v1).

### O que `git init` fez

Criou um repositório git vazio (pasta `.git/`) na raiz do projeto. Isso por
si só não salva nada ainda — só marca a pasta como "sob controle de versão".
O próximo passo natural seria um primeiro commit, mas isso eu não faço sem
te avisar antes (é uma ação que, uma vez feita errado — ex. commitando algo
sensível — dá mais trabalho pra desfazer do que só esperar sua confirmação).

### Estado do projeto ao final da Fase 0 (antes do adendo abaixo)

```
mapa-amazonia/
├── .venv/              # ambiente isolado, não versionado
├── .git/                # repositório git, ainda sem commits
├── pyproject.toml       # as 5 dependências declaradas
├── uv.lock              # versões exatas resolvidas (garante reprodutibilidade)
├── CLAUDE.md
├── config.py
├── ESTUDO.md            # este arquivo
├── plano.html
├── scripts/             # ainda vazio
├── data/{raw,processed}/ # ainda vazio
└── site/                 # ainda vazio
```

**Critério de pronto da Fase 0 (do plano):** ambiente criado, dependências
instaladas, git inicializado. ✅ Feito.

### Adendo (05/09/2026) — de `config.py` solto pra pacote instalável

Isto não estava no plano original. Depois de escrever `scripts/01_temperatura_ar.py`
(Fase 1, ver abaixo), o script não conseguia `import config` — e a correção
que eu apliquei na hora (um `sys.path.insert(...)` no topo do script) recebeu
uma crítica justa: funcionaria, mas repetiria a mesma gambiarra em cada um
dos 5 scripts do projeto, e é frágil (depende de contar quantas pastas subir
a partir de cada arquivo). A pergunta certa foi "não seria melhor repensar a
estrutura de pastas?" — e era.

**O problema de raiz.** Quando você roda um arquivo Python diretamente
(`python scripts/01_x.py`), o Python só sabe procurar `import` dentro da
pasta que contém *esse arquivo* — não na pasta onde você está no terminal,
nem em nenhum outro lugar do projeto. `config.py` morava na raiz; os scripts
moram em `scripts/`; então cada script via a raiz como "estranha".

**A solução correta, não a remendada.** Transformar o projeto num pacote
Python de verdade e instalá-lo dentro do próprio ambiente virtual, do mesmo
jeito que `pandas` ou `requests` estão instalados nele. Uma vez instalado
assim, `import mapa_amazonia.config` funciona de **qualquer** arquivo do
projeto, rodado de **qualquer** pasta — porque deixa de ser "um arquivo
vizinho" e passa a ser "uma biblioteca disponível no ambiente", igual às
bibliotecas de terceiros.

**O que mudou, em três passos:**

1. `config.py` foi movido para dentro de uma pasta com nome de pacote:
   `src/mapa_amazonia/config.py`, com um `src/mapa_amazonia/__init__.py`
   vazio do lado (é o `__init__.py` vazio que faz uma pasta comum virar,
   para o Python, um "pacote" importável).

   Dentro do `config.py`, a linha que calcula a raiz do projeto (usada para
   montar os caminhos de `data/` e `site/`) precisou subir mais um nível,
   porque o arquivo agora está duas pastas mais fundo:

   ```python
   # antes (config.py na raiz):
   RAIZ = Path(__file__).parent

   # depois (config.py em src/mapa_amazonia/config.py):
   RAIZ = Path(__file__).resolve().parents[2]
   # parents[0] = src/mapa_amazonia, parents[1] = src, parents[2] = raiz
   ```

2. `pyproject.toml` ganhou uma seção que faltava — o `[build-system]`. Sem
   isso, o `uv init --bare` original criava só uma "lista de dependências",
   não um pacote de verdade (por isso o `sys.path` hack era necessário
   antes: não havia nada para instalar). `hatchling` é a ferramenta que sabe
   empacotar uma pasta Python; `packages = ["src/mapa_amazonia"]` diz a ela
   onde está o código:

   ```toml
   [build-system]
   requires = ["hatchling"]
   build-backend = "hatchling.build"

   [tool.hatch.build.targets.wheel]
   packages = ["src/mapa_amazonia"]
   ```

3. `uv sync` instalou o próprio projeto no `.venv`, em **modo editável**
   (`mapa-amazonia==0.1.0 (from file:///...)` no log). "Editável" quer dizer:
   não é uma cópia congelada — o Python lê o código direto de
   `src/mapa_amazonia/`, então qualquer edição no arquivo já vale na próxima
   vez que algo importar `mapa_amazonia`, sem precisar reinstalar.

   Com isso, o import em qualquer script deixou de precisar de gambiarra:

   ```python
   # antes:
   import sys
   from pathlib import Path
   sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
   from config import DIR_PROCESSED

   # depois:
   from mapa_amazonia.config import DIR_PROCESSED
   ```

**Por que isto é mais robusto, não só mais bonito.** O `sys.path` hack
dependia de contar corretamente quantas pastas subir a partir de *cada*
arquivo — se um script um dia se movesse de pasta (ex.: para uma subpasta de
`scripts/`), o número quebraria silenciosamente ou com um erro confuso. O
pacote instalado não depende de onde o arquivo que faz o `import` está: ele
resolve pelo nome (`mapa_amazonia`), do mesmo jeito que `import pandas`
funciona em qualquer lugar do projeto. É a mesma solução que qualquer projeto
Python "de verdade" usa — não é over-engineering para este projeto pequeno,
é o comportamento padrão que só não veio de fábrica porque `uv init --bare`
propositalmente pula essa parte (ela é "opcional" até você precisar importar
algo entre arquivos, que foi exatamente o que aconteceu na Fase 1).

**Estrutura de pastas, atualizada:**

```
mapa-amazonia/
├── .venv/
├── .git/
├── pyproject.toml        # agora com [build-system] + lista de pacotes
├── uv.lock
├── CLAUDE.md
├── ESTUDO.md
├── plano.html
├── src/
│   └── mapa_amazonia/
│       ├── __init__.py    # vazio — só marca a pasta como pacote
│       └── config.py       # o config antigo, com RAIZ ajustado
├── scripts/
│   └── 01_temperatura_ar.py
├── data/{raw,processed}/
└── site/
```

---

## Fase 1 — Primeira série temporal real (Open-Meteo)

### Objetivo desta fase

Um gráfico da temperatura do ar em Manaus, de 1940 até hoje. Sem Earth Engine
ainda — o motivo é pedagógico: isolar os conceitos de `requests` + `pandas` +
datas da complexidade extra do satélite. Se algo quebrasse aqui, o erro seria
só de Python puro. E o resultado já é uma camada real do produto final: o
"termômetro geral da cidade" que o `CLAUDE.md` cita como validação para as
camadas de satélite (que cobrem só 2001–2025 e são espacialmente granulares,
mas pontuais no tempo).

Arquivo: `scripts/01_temperatura_ar.py`. Import do config, depois do adendo
acima: `from mapa_amazonia.config import DIR_PROCESSED`.

### Antes dos blocos: a sintaxe `nome: Tipo` e `-> Tipo`

Toda função a partir daqui usa uma sintaxe que ainda não tinha aparecido:

```python
def buscar_dados_diarios(data_inicio: str, data_fim: str) -> dict:
#                        ^^^^^^^^^^^^^^^^  ^^^^^^^^^^^^^^^     ^^^^
#                        parâmetro: tipo   parâmetro: tipo     tipo de retorno
```

**A regra geral:** `nome_do_parametro: Tipo` depois de cada argumento diz que
tipo de valor a função *espera* receber ali; `-> Tipo` depois dos parênteses
diz que tipo de valor ela *devolve* no `return`. Isso se chama **type hint**
("dica de tipo"), existe desde o Python 3.5, e é **opcional** — nada na
linguagem obriga a escrever, e nada impede de escrever errado.

**O detalhe mais importante: isso não é validado quando o código roda.**
Diferente de Java ou TypeScript, o Python não checa a anotação em tempo de
execução — ela é lida por humanos (e por ferramentas externas como o
`mypy`), não pelo interpretador. Prova:

```python
def dobro(x: int) -> int:
    return x * 2

dobro("abc")
# Roda sem reclamar da anotação "x: int". Só quebra (ou não) por causa do
# que a linha "x * 2" faz de fato: "abc" * 2 vira "abcabc" — nenhum erro é
# levantado aqui, porque multiplicar texto por número é válido em Python,
# mesmo violando a promessa da anotação.
```

**Então é só um comentário chique?** Não exatamente. Um comentário (`#
texto`) é descartado antes do Python "entender" o arquivo — o interpretador
nunca chega a vê-lo como dado. Um type hint é sintaxe de verdade: o Python
guarda essas anotações num dicionário, grudado na própria função, acessível
em tempo real:

```python
def soma(a: int, b: int) -> int:
    return a + b

print(soma.__annotations__)
# {'a': <class 'int'>, 'b': <class 'int'>, 'return': <class 'int'>}
```

Esse dicionário existir de verdade é o que permite outras ferramentas
fazerem algo com ele — um verificador estático como `mypy` lê essas
anotações e acusa erro *antes* de rodar o programa; bibliotecas como
Pydantic ou FastAPI usam esse mesmo dicionário em tempo de execução para
validar ou converter dados de verdade. O Python "puro" (o que a gente está
usando aqui, rodando com `uv run`) ignora esse dicionário — não o consulta
pra decidir nada —, mas o ecossistema em volta não. Na prática, para o
comportamento deste projeto especificamente, o efeito é o mesmo de um
comentário: documentação que não muda o que o código faz.

Ou seja: a anotação é uma promessa para quem lê o código (inclusive você
mesmo, depois), não uma trava de segurança. O motivo de eu usar é
legibilidade — numa função como `montar_dataframe(json_bruto: dict) ->
pd.DataFrame`, a assinatura sozinha já diz "entra dicionário, sai
DataFrame", sem precisar ler o corpo inteiro para descobrir. Num pipeline
onde cada função passa uma "forma" de dado adiante, isso ajuda a não se
perder.

Duas variações que vão aparecer bastante:

- **`pd.DataFrame | None`** — o `|` significa "ou": o valor é um `DataFrame`,
  **ou** é `None` (o jeito do Python de dizer "nenhum valor"). Usado em
  `atualizar_serie(existente: pd.DataFrame | None)` porque
  `carregar_dados_existentes()` pode devolver um `DataFrame` (achou o
  parquet) ou `None` (primeira execução, nada salvo ainda) — e quem lê a
  assinatura já sabe que precisa tratar os dois casos. (Sintaxe do Python
  3.10+; versões mais antigas escreviam `Optional[pd.DataFrame]`, equivalente.)
- **`tuple[pd.DataFrame, pd.DataFrame]`** — `tuple` é uma sequência fixa de
  valores (tipo `(1, 2)`); o que vai dentro dos colchetes diz quantos itens
  tem e de que tipo é cada um. Usado em `agregar_mensal_e_anual(...) ->
  tuple[...]` porque a função sempre devolve exatamente dois DataFrames, na
  ordem `return mensal, anual`.
- **`-> None`** — a função não devolve nada útil; existe pelo *efeito* que
  causa (salvar um arquivo, imprimir algo), não por um valor que alguém vai
  reaproveitar depois. Aparece em `salvar_parquet`, `gerar_grafico` e `main`.

**Por que dá pra descrever "dois valores de retorno" com um tipo só.** Não
são dois type hints — é **um** tipo (`tuple[...]`) que descreve quantos
valores tem dentro e de que tipo é cada um. O que possibilita isso é como o
Python trata `return` com vírgula: a vírgula sozinha já cria uma tupla.

```python
def dois_valores() -> tuple[int, str]:
    return 42, "ola"          # equivalente a: return (42, "ola")

resultado = dois_valores()
print(type(resultado), resultado)   # <class 'tuple'> (42, 'ola')

a, b = dois_valores()                # "desempacota" a tupla em duas variáveis
print(a, b)                          # 42 ola
```

É exatamente o que `mensal, anual = agregar_mensal_e_anual(df)` faz no
`main()`: a função devolve uma tupla só; a vírgula do lado esquerdo do `=`
desempacota essa tupla em duas variáveis separadas. E escala: `tuple[int,
str, float]` descreveria uma tupla de três valores, um de cada tipo — a
posição dentro dos colchetes corresponde à posição na tupla devolvida.

**Quem lê essas anotações, na prática:** (1) você, lendo a assinatura sem
precisar abrir o corpo da função; (2) o editor de código, que lê essas
mesmas anotações pra te mostrar a dica ao passar o mouse em cima do nome da
função (hover) — isso é o editor fazendo isso, não o `mypy`; (3) o `mypy` (ou
outro verificador estático), rodado à parte como uma ferramenta de linha de
comando, que aponta erro quando o código não respeita o que a anotação
prometeu — sem rodar o programa de verdade.

### O que é a Open-Meteo Archive API

Uma API HTTP gratuita, sem chave de acesso, que devolve reanálise climática
ERA5 (dados meteorológicos reconstruídos a partir de modelos + observações,
não de uma estação específica) desde 1940. "API HTTP" aqui quer dizer: você
manda um pedido (`GET`) para uma URL com parâmetros, e recebe de volta texto
no formato JSON.

### Bloco 1 — `buscar_dados_diarios()`

```python
def buscar_dados_diarios(data_inicio: str, data_fim: str) -> dict:
    parametros = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "start_date": data_inicio,
        "end_date": data_fim,
        "daily": "temperature_2m_mean",
        "timezone": "America/Manaus",
    }
    resposta = requests.get(URL_ARCHIVE_API, params=parametros, timeout=60)
    resposta.raise_for_status()
    return resposta.json()
```

Quatro ideias aqui:

- `requests.get(url, params=dict)` monta a query string sozinho — não
  precisamos escrever `"?latitude=-3.13&longitude=..."` manualmente nem nos
  preocupar em escapar caracteres especiais.
- `data_inicio` e `data_fim` são **parâmetros da função**, não valores fixos
  escritos aqui dentro. Isso é o que permite chamar esta mesma função tanto
  para "o histórico inteiro" quanto para "só os dias novos" — ver Bloco 5.
- `raise_for_status()` é uma checagem defensiva: se a API responder com erro
  (por exemplo, parâmetro inválido), essa linha levanta uma exceção ali mesmo.
  Sem ela, o script seguiria tentando ler um JSON de erro como se fosse dado
  válido, e o erro real só apareceria (confuso) mais adiante.
- `timeout=60`: sem isso, se a API travar, o script ficaria esperando pra
  sempre. Com timeout, ele desiste depois de 60s e levanta erro.

### Bloco 2 — `montar_dataframe()`: por que o JSON é "colunar"

```python
def montar_dataframe(json_bruto: dict) -> pd.DataFrame:
    diario = json_bruto["daily"]
    df = pd.DataFrame({
        "data": diario["time"],
        "temp_media_c": diario["temperature_2m_mean"],
    })
    df["data"] = pd.to_datetime(df["data"])
    return df
```

A Open-Meteo devolve o bloco `"daily"` assim (resumido):

```json
{
  "daily": {
    "time": ["1940-01-01", "1940-01-02", ...],
    "temperature_2m_mean": [25.3, 24.9, ...]
  }
}
```

Ou seja: uma lista por variável, todas do mesmo tamanho, alinhadas por
posição (o dia N de `time` corresponde ao dia N de `temperature_2m_mean`).
Isso é diferente de uma lista de "um dicionário por dia" — e é exatamente o
formato que `pd.DataFrame({"coluna": lista, ...})` espera: cada chave do
dicionário vira uma coluna, cada posição da lista vira uma linha. Por isso a
conversão é direta, sem loop.

`diario["time"]` e `diario["temperature_2m_mean"]` são simplesmente as duas
listas de dentro do JSON, acessadas por nome (como um dicionário Python
comum — o `.json()` do `requests`, lá no Bloco 1, já converteu o texto JSON
num dict/list Python de verdade, então não há nada de mágico aqui).

A linha `df["data"] = pd.to_datetime(df["data"])` existe porque a API devolve
datas como texto (`"1940-01-01"`), não como data de verdade. Sem essa
conversão, o Bloco 4 (`resample`) não funcionaria — ele precisa saber que uma
data vem antes da outra cronologicamente, não comparar como texto (em texto,
`"2001-03-15" < "2001-03-2"` daria o resultado errado, por exemplo — string
compara caractere a caractere).

### Bloco 3 — `atualizar_serie()`: busca incremental

**O problema que este bloco resolve:** a primeira versão do script buscava
sempre de 1940 até hoje, mesmo que o arquivo já tivesse os dados de ontem
salvos — rodar de novo daqui a um mês rebaixaria 86 anos de dado só para
adicionar 30 dias novos. Isso não é só ineficiente: é desnecessário chamar
uma API de graça repetidamente pelo mesmo dado que você já tem em disco.

```python
def atualizar_serie(existente: pd.DataFrame | None) -> pd.DataFrame:
    hoje = pd.Timestamp.today().normalize()

    if existente is None:
        print(f"Nenhum dado salvo ainda. Buscando desde {INICIO_HISTORICO}.")
        data_inicio = pd.Timestamp(INICIO_HISTORICO)
    else:
        ultimo_dia_salvo = existente["data"].max()
        data_inicio = ultimo_dia_salvo + pd.Timedelta(days=1)
        print(f"Dado salvo vai até {ultimo_dia_salvo.date()}.")

    if data_inicio > hoje:
        print("Já está atualizado — nada para buscar.")
        return existente

    json_bruto = buscar_dados_diarios(
        data_inicio.strftime("%Y-%m-%d"), hoje.strftime("%Y-%m-%d")
    )
    novos = montar_dataframe(json_bruto)

    antes = len(novos)
    novos = novos.dropna(subset=["temp_media_c"])
    if len(novos) < antes:
        print(f"{antes - len(novos)} dia(s) recente(s) ainda sem dado — descartado(s) por ora.")

    print(f"{len(novos)} dia(s) novo(s) baixado(s).")

    if existente is None:
        return novos
    return (
        pd.concat([existente, novos])
        .drop_duplicates(subset="data")
        .sort_values("data")
        .reset_index(drop=True)
    )
```

Passo a passo:

1. **`existente is None`?** É o sinal de "primeira execução" — vem de
   `carregar_dados_existentes()`, que devolve `None` quando
   `manaus_ar.parquet` ainda não existe em disco. Só neste caso buscamos o
   histórico completo desde `INICIO_HISTORICO` ("1940-01-01").
2. **Senão, `data_inicio = ultimo_dia_salvo + pd.Timedelta(days=1)`** — o dia
   seguinte ao último que já temos salvo. `pd.Timedelta(days=1)` é "somar um
   dia" de um jeito que o pandas entende como data, não como número (não dá
   pra somar `1` direto a uma data).
3. **`if data_inicio > hoje: ... return existente`** — se o último dia salvo
   já é hoje (ou o script já rodou hoje), não há nada de novo para buscar.
   Devolve os dados existentes sem chamar a API. Isso responde diretamente à
   pergunta: rodar de novo no mesmo dia (ou daqui a uma semana, buscando só
   a semana) não volta a 1940.
4. **`novos.dropna(subset=["temp_media_c"])`** — proteção contra a reanálise
   ERA5 ainda não ter processado os dias mais recentes (ela tem uma pequena
   defasagem). Se pedíssemos "até hoje" e a API devolvesse os últimos 1-2
   dias como nulo, salvaríamos lixo no parquet. Descartando essas linhas
   agora, elas simplesmente serão buscadas de novo (e virão preenchidas) na
   próxima execução, quando o dado já estiver disponível.
5. **`pd.concat([existente, novos]).drop_duplicates(subset="data")...`** —
   junta o que já tínhamos com o que acabou de chegar, remove qualquer
   duplicata por data (defesa extra, caso o intervalo buscado se sobreponha
   por engano com o que já existia) e reordena por data. `reset_index` só
   limpa a numeração de linhas para ficar sequencial de novo (o `concat`
   deixaria índices repetidos/fora de ordem).

**Testado na prática:** cortei manualmente o parquet salvo para conter só
até 2019-12-31 e rodei o script de novo. Ele reconheceu "dado salvo vai até
2019-12-31", buscou só 2020-01-01 em diante (2440 dias, não os 31660 do
histórico inteiro), e o resultado final bateu byte a byte com o dataset
original (mesmo total de linhas, mesmo intervalo de datas, zero duplicatas).

### Bloco 4 — `agregar_mensal_e_anual()`: o `resample`

```python
def agregar_mensal_e_anual(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    df_indexado = df.set_index("data")
    mensal = df_indexado.resample("MS").mean()
    anual = df_indexado.resample("YS").mean()
    return mensal, anual
```

`resample()` é o método do pandas para "trocar a granularidade de uma série
temporal" — aqui, de diário para mensal/anual. Só funciona quando a coluna de
data é o **índice** do DataFrame (por isso `set_index("data")` antes). `"MS"`
e `"YS"` são códigos de frequência do pandas (Month Start / Year Start): cada
grupo de dias que cai no mesmo mês (ou ano) vira uma linha só, com a média.

Isto é literalmente o que o projeto inteiro faz depois com dados de satélite
— agregar composições de 8/16 dias em médias mensais. Aprender aqui, com uma
API simples, é o ponto da fase. Repare que esta função sempre recebe o `df`
**completo** (existente + novo, já juntado pelo Bloco 3) — mensal/anual são
recalculados do zero a cada execução, o que é barato, em vez de tentar
atualizar incrementalmente uma média já calculada (o que seria mais
complicado e mais fácil de errar).

### Bloco 5 — salvar só o diário, não o mensal/anual

```python
def salvar_parquet(df_diario: pd.DataFrame) -> None:
    DIR_PROCESSED.mkdir(parents=True, exist_ok=True)
    df_diario.to_parquet(CAMINHO_PARQUET)
    print(f"Salvo: {CAMINHO_PARQUET}")
```

O script salva apenas `data/processed/manaus_ar.parquet` (a série diária).
Mensal e anual não ganham arquivo próprio: são baratos de recalcular a partir
do diário com `resample()` sempre que precisar, então guardá-los duplicaria
dado sem necessidade. É também esse mesmo arquivo diário que `atualizar_serie`
lê de volta na próxima execução, através de `carregar_dados_existentes()`:

```python
def carregar_dados_existentes() -> pd.DataFrame | None:
    if CAMINHO_PARQUET.exists():
        return pd.read_parquet(CAMINHO_PARQUET)
    return None
```

Parquet (não CSV) porque é o formato de armazenamento decidido para o
projeto todo — mais compacto e preserva o tipo de cada coluna (CSV guarda
tudo como texto e cada leitor precisa "adivinhar" os tipos de novo, o que já
teria causado bug aqui: `df["data"]` viria de volta como texto, não como data).

### A armadilha do `import`

Rodando este script pela primeira vez, apareceu `ModuleNotFoundError: No
module named 'config'`. Isso levou a uma revisão de estrutura de pastas —
ver o **adendo no fim da seção da Fase 0**, acima, que documenta o problema
e a solução adotada (pacote instalável em vez de `sys.path` manual).

### Resultado

```
Buscando dados na Open-Meteo Archive API...
Nenhum dado salvo ainda. Buscando desde 1940-01-01.
31660 dia(s) novo(s) baixado(s).
Salvo: data/processed/manaus_ar.parquet
Salvo: data/processed/manaus_ar_anual.png
```

O gráfico (`data/processed/manaus_ar_anual.png`) mostra a média anual
oscilando ao redor de 26 °C entre 1940 e ~1990, e depois subindo com
tendência visível até cerca de 27,5–28 °C nos anos 2020 — exatamente o
critério de pronto do plano ("tendência de aquecimento visível ao longo das
décadas"). O ponto de 2026 é um ano parcial (só até setembro), então vale
não superinterpretar o último ponto isoladamente.

**Critério de pronto da Fase 1 (do plano):** ✅ gráfico existe e mostra
tendência de aquecimento.

---

## Fase 2 — Earth Engine: conta e o primeiro número

### Objetivo desta fase

Imprimir a temperatura de superfície média de Manaus em julho de 2020. Um
número só — mas o caminho até ele é o conceito mais importante do projeto
inteiro: o Earth Engine não roda nada na sua máquina.

Arquivo: `scripts/02_ee_primeiro_teste.py`.

### O conceito central: client vs. server

`ee.Image`, `ee.ImageCollection`, `ee.Geometry`, `ee.Number` **não contêm
dado nenhum**. São *descrições* de um cálculo que ainda não aconteceu — uma
receita, não o prato pronto. O cálculo de verdade só roda no servidor do
Google quando você chama `.getInfo()` (ou faz um `Export`). Até lá, tudo que
você "constrói" com objetos `ee.*` fica só descrito, encadeado, esperando.

Três consequências práticas:

- `print(minha_imagem)` imprime a descrição do objeto (algo tipo
  `<ee.image.Image object at 0x...>` ou uma representação JSON da receita),
  **não** os valores de pixel.
- Não dá pra usar `if`, `for` ou `len()` do Python direto num objeto `ee.*`
  — porque nesse momento o valor ainda não existe no seu computador para o
  Python testar. As operações precisam ser as do próprio Earth Engine
  (`.map()`, `ee.Filter`, `.size()` do lado do servidor), executadas
  remotamente.
- Misturar um valor Python puro com um objeto `ee.*` às vezes funciona
  (o Earth Engine converte sozinho) e às vezes dá erro difícil de entender.
  Na dúvida, converte explicitamente (`ee.Number(x)`).

Isso explica por que o script inteiro (abaixo) só tem **uma** linha que de
fato "sai" pro servidor e volta com um número: `.getInfo()`, no fim.

### Bloco 1 — `inicializar()`

```python
def inicializar() -> None:
    ee.Initialize(project=EE_PROJECT_ID)
```

`ee.Initialize` lê a credencial já salva em
`~/.config/earthengine/credentials` (gerada rodando `earthengine
authenticate` no seu terminal — um passo manual, feito uma vez por máquina,
que abre o navegador pra você logar com a conta Google dona do projeto) e
associa toda chamada seguinte ao seu Project ID (`EE_PROJECT_ID =
"mapa-amazonia"`, em `config.py`). Sem isso, qualquer `ee.*` daria erro de
"não inicializado".

### Bloco 2 — `montar_regiao()`

```python
def montar_regiao() -> ee.Geometry:
    return ee.Geometry.Rectangle(BBOX)
```

`BBOX` (de `config.py`) é `[-60.20, -3.20, -59.75, -2.85]`, na ordem
[oeste, sul, leste, norte] — exatamente a ordem que `ee.Geometry.Rectangle`
espera. Repare que isto **não busca nada ainda**: é só a descrição de um
retângulo. Ele só é "usado" de verdade quando entra num `filterBounds` ou
`reduceRegion`, no bloco seguinte.

### Bloco 3 — `temperatura_media_julho_2020()`: os três passos server-side

```python
def temperatura_media_julho_2020(regiao: ee.Geometry) -> float:
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

    valor_bruto = resultado.get("LST_Day_1km").getInfo()

    return valor_bruto * ESCALA_LST - ZERO_ABSOLUTO
```

Três passos, cada um uma operação encadeada, ainda sem nenhum número na sua
máquina:

1. **Filtrar a coleção.** `ee.ImageCollection(COLECAO_LST)` é a coleção
   inteira do MOD11A2 (composições de 8 dias, cobrindo 2000–2026).
   `.filterDate("2020-07-01", "2020-08-01")` reduz isso às composições que
   caem dentro de julho de 2020 (o segundo argumento é exclusivo — por isso
   `"2020-08-01"` e não `"2020-07-31"`). `.filterBounds(regiao)` reduz mais,
   descartando qualquer imagem que nem toque o bbox de Manaus.
   `.select("LST_Day_1km")` descarta todas as outras bandas do dataset
   (existem várias — qualidade, horário de passagem, banda noturna — ver
   Fase 3), ficando só com a temperatura de superfície diurna.
2. **`.mean()`** colapsa a coleção filtrada (tipicamente 4 composições de 8
   dias, já que julho tem ~31 dias) numa única imagem, tirando a média
   pixel a pixel ao longo do tempo.
3. **`.reduceRegion(...)`** colapsa essa imagem única numa média espacial:
   todos os pixels dentro do bbox (`geometry=regiao`) viram um número só
   (`reducer=ee.Reducer.mean()`). `scale=RESOLUCAO_M` (1000, de `config.py`)
   diz em que resolução o servidor deve reamostrar antes de calcular — bate
   com a resolução nativa do MOD11A2, então não há reamostragem de verdade
   acontecendo aqui.

`reduceRegion` devolve um dicionário (`ee.Dictionary`, ainda do lado do
servidor) com uma chave por banda selecionada — aqui, só uma:
`"LST_Day_1km"`. `resultado.get("LST_Day_1km")` pega essa entrada — ainda
uma descrição, um `ee.ComputedObject`, não um número Python.

**A linha que realmente sai da sua máquina e volta:**
`.getInfo()`, no fim de `resultado.get("LST_Day_1km").getInfo()`. É só aqui
que a receita inteira (filtrar → média temporal → média espacial) é enviada
pro servidor, executada lá, e o resultado — um float puro do Kelvin×50 —
volta pra sua máquina como um número Python de verdade.

**A conversão final:** `valor_bruto * ESCALA_LST - ZERO_ABSOLUTO`. O MOD11A2
guarda a temperatura como Kelvin multiplicado por 50 (`ESCALA_LST = 0.02`
desfaz isso), depois `- ZERO_ABSOLUTO` (273.15) converte de Kelvin para
Celsius. Os dois fatores vêm do `config.py`, seção 4 — errar qualquer um dos
dois é, no próprio comentário do arquivo, "o erro clássico do projeto"
(esquecer a escala dá um número na casa dos milhares; esquecer o zero
absoluto dá um número na casa dos 300).

### Armadilha real (de sistema, não do Earth Engine): certificado SSL

Autenticar (`earthengine authenticate`, rodado por você no seu terminal)
funcionou, mas a primeira tentativa de trocar o código de autorização por
um token deu:

```
ssl.SSLCertVerificationError: [SSL: CERTIFICATE_VERIFY_FAILED]
unable to get local issuer certificate
```

Isto não tem nada a ver com Earth Engine — é um problema conhecido do
instalador oficial do Python para macOS (python.org, não Homebrew): ele não
conecta o Python recém-instalado à cadeia de certificados raiz do sistema
automaticamente. Qualquer biblioteca que use `urllib` puro (como o cliente
OAuth do `earthengine-api`) esbarra nisso; bibliotecas que usam `requests`
(como o script da Fase 1) não, porque o `requests` já embute o pacote
`certifi` e não depende da configuração de SSL do sistema.

Diagnóstico: `ssl.get_default_verify_paths()` apontava para um arquivo
(`.../Python.framework/Versions/3.14/etc/openssl/cert.pem`) que não existia.

Correção: o próprio instalador do Python já vem com um script pronto para
isso —

```bash
"/Applications/Python 3.14/Install Certificates.command"
```

Ele faz `pip install --upgrade certifi` (na instalação *base* do Python
3.14, não no `.venv` do projeto) e cria um link do arquivo de certificado
que o Python espera para o pacote `certifi` recém-instalado. É um fix de
sistema, de uma vez só por máquina — não precisa rodar de novo por projeto.

### Resultado

```
Temperatura média de superfície em Manaus, julho/2020: 29.41 °C
```

**Critério de pronto da Fase 2 (do plano):** ✅ o número está entre ~28°C e
~40°C — a faixa que o plano definia como plausível para julho (mês seco,
mais quente) em Manaus. Se tivesse dado 300 e pouco, teria faltado subtrair
o zero absoluto; se desse 6000, teria faltado multiplicar pelo fator 0.02.

---

## Fase 3 — Temperatura mensal, 2001-2025

### Objetivo desta fase

Uma tabela com temperatura de superfície média — dia e noite, separadas —
por célula da grade, por mês, ao longo de 25 anos (300 meses). É a primeira
camada "de verdade" do produto final.

Arquivos: `src/mapa_amazonia/grade.py` (novo módulo, compartilhado com as
próximas fases) e `scripts/03_lst_mensal.py`.

### Por que um módulo `grade.py` separado, em vez de código dentro do script

Fase 4 (NDVI) e Fase 5 (montagem final) vão precisar exatamente da mesma
grade — mesmas células, mesmos `cell_id` — para o cruzamento
temperatura×vegetação ser um `join` simples por célula (decisão da v1). Se
cada script construísse a grade do seu próprio jeito, um desalinhamento
sutil entre elas (uma reprojeção ligeiramente diferente, por exemplo)
quebraria o join sem dar erro nenhum — só números errados. Construir uma
vez, num módulo importável, e reusar, evita essa classe de bug — mesmo
raciocínio do adendo à Fase 0 (pacote em vez de repetir código).

### `construir_grade()`: cobrindo o bbox com células de 1 km

```python
def construir_grade() -> ee.FeatureCollection:
    regiao = ee.Geometry.Rectangle(BBOX)
    projecao = ee.Projection("EPSG:3857").atScale(RESOLUCAO_M)
    grade_bruta = regiao.coveringGrid(projecao)
    return grade_bruta.map(_nomear_celula)
```

`coveringGrid(projecao)` é um método do Earth Engine que já faz exatamente
o que o nome diz: cobre uma geometria com uma grade regular de células,
numa projeção e escala dadas. `EPSG:3857` (Web Mercator) é necessária porque
`RESOLUCAO_M = 1000` só faz sentido como "1000 metros" numa projeção que usa
metro como unidade — graus de latitude/longitude (a projeção "natural" do
bbox, EPSG:4326) não têm um tamanho físico fixo (perto do equador, 1 grau de
longitude ≈ 111 km; perto dos polos, quase zero).

`_nomear_celula` dá a cada célula um `cell_id` a partir do centro dela:

```python
def _nomear_celula(celula: ee.Feature) -> ee.Feature:
    centro = ee.Feature(celula).geometry().centroid(1)
    coordenadas = centro.coordinates()
    lon = coordenadas.get(0)
    lat = coordenadas.get(1)
    cell_id = (
        ee.String("c_")
        .cat(ee.Number(lon).format("%.4f"))
        .cat("_")
        .cat(ee.Number(lat).format("%.4f"))
    )
    return celula.set({"cell_id": cell_id, "lon": lon, "lat": lat})
```

Por que não usar o `system:index` que o Earth Engine já dá de graça a cada
feature de uma coleção? Porque não há garantia documentada de que esse
índice interno seja estável entre chamadas diferentes — um `cell_id`
calculado a partir da posição geográfica real da célula é auto-descritivo
(dá pra saber onde a célula fica só olhando o nome) e não depende de nenhum
detalhe de implementação interno do Earth Engine.

`.centroid(1)` — o `1` é a tolerância de erro em metros que o cálculo do
centroide tolera (uma otimização de performance do Earth Engine; para
retângulos pequenos como estes, é irrelevante). `ee.String(...).cat(...)`
concatena texto do lado do servidor (o equivalente ao `+` de strings em
Python, mas em `ee.String`, porque estamos montando isso a partir de
números que só existem no servidor até aqui).

**Resultado:** 2.040 células — na mesma ordem de grandeza da estimativa do
plano (~1.950); a diferença vem da grade cobrir o bbox por completo,
passando um pouco da borda em vez de cortar exatamente nela.

### A máscara de qualidade (QC) — bits dentro de um número

```python
def mascarar_por_qc(imagem: ee.Image, banda_dado: str, banda_qc: str) -> ee.Image:
    qc = imagem.select(banda_qc)
    qualidade_boa = qc.bitwiseAnd(3).eq(0)
    return imagem.select(banda_dado).updateMask(qualidade_boa)
```

O MOD11A2 não marca "esse pixel é ruim" numa coluna separada — ele guarda
essa informação **dentro dos bits** de um número inteiro (`QC_Day`/
`QC_Night`), pra economizar espaço. Os 2 bits menos significativos desse
número são a "flag obrigatória" do produto: `00` = boa qualidade, LST
produzida; qualquer outro valor (nuvem cobrindo o pixel, ou LST não
produzida por outro motivo) significa "não confie neste valor".

`bitwiseAnd(3)` isola exatamente esses 2 bits, ignorando o resto do número
(`3` em binário é `11` — "E" bit a bit com `11` zera tudo que não são os
dois últimos bits). `.eq(0)` compara o resultado com `00`, virando uma
máscara booleana (verdadeiro = mantém o pixel, falso = descarta).
`.updateMask(...)` aplica essa máscara na banda de dado: pixels descartados
viram "sem dado" (não zero — sem dado mesmo, para não contaminar a média
com zeros falsos).

**Simplificação assumida:** só a flag obrigatória (bits 0-1) é checada. O
produto MODIS também guarda, em outros bits, um erro estimado de
emissividade e de LST — uma versão mais rigorosa filtraria esses também.
Não fizemos isso na v1 para manter o script neste nível de complexidade;
fica registrado como possível refinamento futuro.

### De 8 em 8 dias pra média mensal, sem loop Python

```python
def construir_imagem_mensal(data_inicio: ee.Date, regiao: ee.Geometry) -> ee.Image:
    data_fim = data_inicio.advance(1, "month")
    colecao_do_mes = (
        ee.ImageCollection(COLECAO_LST)
        .filterDate(data_inicio, data_fim)
        .filterBounds(regiao)
        .map(mascarar_composicao)
    )
    media_bruta = colecao_do_mes.mean()
    return media_bruta.multiply(ESCALA_LST).subtract(ZERO_ABSOLUTO)
```

Um mês normal contém ~4 composições de 8 dias do MOD11A2 (8×4=32, perto dos
28-31 dias do mês — nem sempre exato, porque as composições de 8 dias do
MODIS são fixas no calendário do ano, não realinhadas por mês; alguns meses
pegam 3, outros 4). `.filterDate(data_inicio, data_fim)` seleciona as que
caem dentro do mês; `.map(mascarar_composicao)` aplica a máscara de QC em
**cada uma** delas (a mesma ideia do `.map()` já visto na Fase 1, mas agora
do lado do servidor, sobre uma `ImageCollection` em vez de sobre uma lista
Python); `.mean()` colapsa essas poucas imagens numa só, pixel a pixel —
pixels mascarados em uma composição simplesmente não entram na média
daquele pixel, sem precisar de nenhum tratamento especial.

A conversão de escala (`* ESCALA_LST - ZERO_ABSOLUTO`) acontece **aqui**,
antes de reduzir por célula — não depois, em Python. Fazer a conversão uma
vez só, num lugar central, usando as constantes do `config.py`, é mais
seguro do que fazer no script 05 (montar tabelas): menos lugares onde
esquecer um dos dois fatores ("o erro clássico do projeto").

### De imagem mensal pra tabela por célula

```python
def tabela_do_mes(data_inicio, grade, regiao) -> ee.FeatureCollection:
    imagem = construir_imagem_mensal(data_inicio, regiao)
    tabela = imagem.reduceRegions(
        collection=grade, reducer=ee.Reducer.mean(), scale=RESOLUCAO_M
    )
    ano = data_inicio.get("year")
    mes = data_inicio.get("month")
    return tabela.map(lambda celula: celula.set({"ano": ano, "mes": mes}))
```

`reduceRegions` (plural — diferente do `reduceRegion` singular da Fase 2) é
a versão que reduz uma imagem por **cada** feature de uma coleção de uma
vez, em vez de por uma geometria só. Recebe a grade inteira (2.040 células)
e devolve uma linha por célula, cada uma com a média espacial da imagem
mensal dentro daquela célula — muito mais eficiente do que chamar
`reduceRegion` 2.040 vezes num loop.

### Sem loop Python pros 300 meses: `ee.List.sequence` + `.map()`

```python
def construir_tabela_completa(grade, regiao) -> ee.FeatureCollection:
    n_meses = (ANO_FIM - ANO_INICIO + 1) * 12
    data_inicial = ee.Date.fromYMD(ANO_INICIO, 1, 1)
    lista_datas = ee.List.sequence(0, n_meses - 1).map(
        lambda i: data_inicial.advance(i, "month")
    )
    lista_de_tabelas = lista_datas.map(
        lambda data: tabela_do_mes(ee.Date(data), grade, regiao)
    )
    return ee.FeatureCollection(lista_de_tabelas).flatten()
```

`ee.List.sequence(0, 299)` é uma lista `[0, 1, 2, ..., 299]`, mas do lado do
servidor (uma `ee.List`, não uma lista Python). `.map(lambda i:
data_inicial.advance(i, "month"))` transforma cada número numa data —
"o mês 0 depois de 2001-01-01" = 2001-01-01, "o mês 1" = 2001-02-01, etc.
— sem nunca ter 300 valores na sua máquina ao mesmo tempo: tudo isso é uma
receita, executada só quando a exportação (abaixo) mandar rodar de verdade.

O segundo `.map()` aplica `tabela_do_mes` a cada uma dessas 300 datas,
devolvendo 300 `FeatureCollection`s (uma por mês, ~2.040 linhas cada).
`ee.FeatureCollection(lista_de_tabelas).flatten()` empilha as 300 tabelas
numa só, de ~612 mil linhas (300 × 2.040).

Repare que **nenhum destes `.map()` é um `for` do Python.** Se fosse, o
Python tentaria iterar sobre um objeto `ee.List`/`ee.FeatureCollection` que
não tem valor nenhum ainda no seu computador — exatamente a armadilha
descrita na Fase 2 (client vs. server).

### Validação antes de gastar cota: `validar_contra_fase_2()`

Antes de disparar a exportação dos 300 meses (que tem custo de
processamento de verdade), rodei só julho de 2020 pela grade nova e
comparei com o número da Fase 2 (que tinha sido tirado de outro jeito: uma
`reduceRegion` só, sobre o bbox inteiro de uma vez, sem grade nenhuma):

```
Validação — média por grade em julho/2020: 29.09 °C
(Fase 2, bbox inteiro de uma vez: 29.41 °C)
```

Não bateram exatamente — e não deveriam: a Fase 2 fez a média de **todos os
pixels do bbox de uma vez**; a Fase 3 faz a média de **cada célula
separadamente, depois a média dessas médias** (uma "média de médias"), e as
bordas da grade cobrem uma área ligeiramente diferente do bbox exato. A
diferença de 0,32 °C é pequena o suficiente para confirmar que o cálculo
está certo, não uma coincidência de números parecidos por acaso.

### Exportação assíncrona: por que o script "não termina" na hora

```python
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
    while True:
        status = tarefa.status()
        estado = status["state"]
        print(f"Status da task: {estado}")
        if estado in ("COMPLETED", "FAILED", "CANCELLED"):
            if estado == "FAILED":
                print("Erro:", status.get("error_message"))
            break
        time.sleep(30)
```

`Export.table.toDrive(...)` não exporta nada na hora — ele **descreve** uma
tarefa de exportação e a registra no servidor do Google (`tarefa.start()`).
O processamento de verdade (rodar os 300 meses × 2.040 células) acontece
depois, na infraestrutura do Google, de forma assíncrona: o script Python
poderia terminar imediatamente e o arquivo ainda assim seria gerado, mais
tarde, no Google Drive da conta autenticada.

O plano original pedia para "acompanhar a task no painel do EE"
(https://code.earthengine.google.com/tasks, um site que mostra o status das
suas exportações). Como quem está rodando isto sou eu, sem abrir navegador,
`acompanhar()` faz a mesma coisa por código: pergunta `tarefa.status()` a
cada 30 segundos e só sai do loop quando o estado deixa de ser
"em andamento" (`RUNNING`/`READY`).

`selectors=[...]` na exportação restringe o CSV às colunas que interessam —
sem isso, o Earth Engine incluiria também a geometria de cada célula
(um polígono) como coluna, inflando o arquivo sem necessidade (a grade
completa, com geometria, será exportada separadamente como
`grade.geojson`, uma vez só, na Fase 5).

### Primeira exportação (com bug, corrigido logo abaixo)

```
Células na grade: 2040
Validação — média por grade em julho/2020: 29.09 °C (Fase 2, bbox inteiro de uma vez: 29.41 °C)
Task iniciada: PKSUG34PLWXQF4W3EBBV62LK
Status da task: READY
Status da task: RUNNING   (x6, ~3 minutos no total)
Status da task: COMPLETED
```

Task concluída em ~3 minutos — "trabalho leve" na cota gratuita, como o
plano previa. Mas o CSV baixado (ver módulo novo abaixo) revelou um bug real
na hora de conferir os dados.

### Baixando do Drive automaticamente: `src/mapa_amazonia/drive.py`

`Export.table.toDrive` deixa o CSV no Google Drive, não em disco local — é
preciso outro passo pra trazer o arquivo pra `data/raw/`. A credencial que
`earthengine authenticate` criou pediu, desde a autorização original na
Fase 2, o escopo `https://www.googleapis.com/auth/drive` (dá pra conferir
abrindo `~/.config/earthengine/credentials` e olhando a lista `"scopes"`) —
ou seja, já dá acesso de Drive completo, não só Earth Engine. Isso permitiu
automatizar o download, sem pedir nova autenticação e **sem instalar
dependência nova**: `google-api-python-client` e `google-auth` já vêm junto
do `earthengine-api` (conferido em `pyproject.toml`/`uv.lock` antes de
escrever qualquer código que usasse eles).

```python
def baixar_do_drive(nome_arquivo: str, pasta_destino: Path) -> Path:
    credenciais = ee.data.get_persistent_credentials()
    servico = build("drive", "v3", credentials=credenciais)

    busca = servico.files().list(
        q=f"name = '{nome_arquivo}' and trashed = false",
        fields="files(id, name, modifiedTime)",
        orderBy="modifiedTime desc",
        pageSize=1,
    ).execute()
    ...
```

`ee.data.get_persistent_credentials()` é a mesma credencial que o
`ee.Initialize(...)` já usa por baixo dos panos — devolvida como um objeto
`google.oauth2.credentials.Credentials` de verdade, pronto pra passar pra
qualquer outra biblioteca do Google (aqui, a API do Drive via
`googleapiclient.discovery.build`). `orderBy="modifiedTime desc"` +
`pageSize=1` garante que, se houver mais de um arquivo com esse nome no
Drive (ex.: de uma exportação anterior), pega sempre o mais recente.

Módulo compartilhável: Fase 4 (NDVI) vai exportar outro CSV do mesmo jeito,
e reaproveita esta mesma função.

### Armadilha real: `LST_Night_1km` saiu 100% vazio

Conferindo o CSV baixado (612.000 linhas = 2.040 células × 300 meses, batendo
com o esperado), a coluna `LST_Night_1km` estava **nula em todas as
linhas**. `LST_Day_1km` também tinha bem mais nulo do que o esperado
(233.713 de 612.000, ~38%).

Investigação, comparando os valores brutos de `QC_Night` num mês (julho de
2020) contra os de `QC_Day`:

```python
stats_day = qc_day.reduceRegion(ee.Reducer.frequencyHistogram(), regiao, 1000).getInfo()
stats_night = qc_night.reduceRegion(ee.Reducer.frequencyHistogram(), regiao, 1000).getInfo()
# QC_Day:   {0: 631, 2: 492, 65: 791, 81: 27}
# QC_Night: {17: 20, 2: 99, 65: 271, 81: 154}
```

Os números brutos (0, 2, 17, 65, 81...) não são a "flag obrigatória" em si —
são o byte inteiro, com a flag guardada só nos 2 bits menos significativos.
Decodificando (`valor % 4`, o mesmo que `bitwiseAnd(3)`):

- `QC_Day`: `0→0`, `2→2`, `65→1`, `81→1` — aparecem os três valores 0
  (boa qualidade), 1 (outra qualidade) e 2 (nuvem, LST não produzida).
- `QC_Night`: `17→1`, `2→2`, `65→1`, `81→1` — **nunca aparece o valor 0**.

Ou seja: a máscara original (`bitwiseAnd(3).eq(0)`, só aceita flag
exatamente 0) não é um bug de código — o código fazia exatamente o que
dizia. O problema é que essa regra, embora pareça a mais "correta" à
primeira vista, **descarta praticamente toda a LST noturna do MOD11A2**: a
banda noturna deste produto quase nunca recebe a flag "0 = boa qualidade,
sem checagem adicional" — ela normalmente vem marcada "1 = outra qualidade,
recomenda-se checar QA detalhada", mesmo quando o valor é perfeitamente
utilizável. É uma característica conhecida (embora não óbvia) do MOD11A2,
não uma nuance exclusiva deste projeto.

Teste comparando as duas regras, contando pixels válidos num mês:

```python
print('Aceitando só bits=0 (atual):', testar(1))
# {'LST_Day_1km': 1699, 'LST_Night_1km': 0}
print('Aceitando bits=0 ou 1 (proposto):', testar(2))
# {'LST_Day_1km': 1950, 'LST_Night_1km': 605}
```

**Correção:** trocar `.eq(0)` por `.lt(2)` — aceitar flag 0 **ou** 1,
rejeitando só 2 e 3 (os dois únicos valores em que a LST realmente **não
foi produzida**, por nuvem ou outro motivo). É a diferença entre perguntar
"a qualidade foi certificada como ótima?" (rejeita até dado bom, só não
com o carimbo mais alto) e perguntar "esse pixel tem valor de verdade, ou
é buraco?" — a segunda é a pergunta que a máscara deveria responder.

Revalidado contra a Fase 2 depois do fix: 29.37 °C (era 29.09 °C antes) —
mais perto ainda de 29.41 °C, o que faz sentido: menos pixels descartados
por excesso de rigor aproxima o resultado do valor sem máscara nenhuma da
Fase 2.

### Resultado (depois da correção)

```
Validação — média por grade em julho/2020: 29.37 °C (Fase 2: 29.41 °C)
Task iniciada: WSIDXFVXKTFBYKAOLA4ZCVW5 — COMPLETED em ~5 minutos
Baixado: data/raw/lst_mensal_2001_2025.csv
```

Conferido depois de baixado:

```
shape: (612000, 7)
LST_Day_1km:   570.415 de 612.000 preenchidas (93%) — antes do fix: 378.287 (62%)
LST_Night_1km: 227.162 de 612.000 preenchidas (37%) — antes do fix: 0 (0%)

Julho/2020 — média dia:   29.37 °C  (bate com a validação acima)
Julho/2020 — média noite: 23.51 °C  (mais fria que o dia, como esperado)
```

`LST_Day_1km` varia de -7,49 °C a 43,15 °C; `LST_Night_1km` de 2,15 °C a
33,31 °C — os dois extremos frios (-7,49 e 2,15) estão fora da faixa
plausível já definida em `config.py` (`LST_MIN_C = 10.0`). Não filtrei
isso agora: é exatamente o que a Fase 5 ("faixas plausíveis... usadas nas
checagens de sanidade") existe para tratar — poucos pixels-outlier
sobrevivendo à máscara de QC é esperado, e o lugar certo de descartá-los é
na montagem da tabela final, não aqui.

**Critério de pronto da Fase 3 (do plano):** ✅ task concluída, CSV com
2.040 × 300 = 612.000 linhas, validação contra a Fase 2 dentro do esperado,
as duas bandas (dia e noite) de fato preenchidas depois da correção da
máscara de QC.

---

## Fase 4 — NDVI mensal, na mesma grade

### Objetivo desta fase

A camada de vegetação: NDVI médio mensal por célula, 2001-2025, na
**mesma** grade e mesmos `cell_id` da Fase 3 — é isso que torna o
cruzamento temperatura×vegetação um `join` simples por célula, em vez de
duas tabelas que não conversam.

Arquivo: `scripts/04_ndvi_mensal.py`. Estrutura deliberadamente paralela à
da Fase 3 (mesmas etapas: mascarar → média mensal → reduzir por célula →
`ee.List.sequence` pros 300 meses → validar → exportar → acompanhar).

### O que é NDVI

`(NIR − Vermelho) / (NIR + Vermelho)` — um número entre -1 e 1 que mede o
quanto uma superfície reflete luz de um jeito característico de vegetação
viva (muito infravermelho-próximo, pouco vermelho — a clorofila absorve
vermelho pra fotossíntese e a estrutura da folha espalha o
infravermelho-próximo). Floresta densa fica perto de 0,8-0,9; asfalto/solo
exposto perto de 0,1; água dá **negativo** (reflete pouco nas duas bandas,
mas um pouco mais no vermelho que no infravermelho).

### `SummaryQA` do MOD13Q1: mais simples que o QC bit a bit da Fase 3

```python
qualidade_ok = imagem.select("SummaryQA").lte(1)
```

Diferente do `QC_Day`/`QC_Night` do MOD11A2 (informação embutida em bits
dentro de um número, exigindo `bitwiseAnd`), o `SummaryQA` do MOD13Q1 já
vem como um número pequeno direto: 0 = ótimo, 1 = bom, 2 = nuvem/neve,
3 = inválido. `.lte(1)` ("less than or equal", menor ou igual) mantém 0 e
1, descarta 2 e 3 — mais simples de ler que o equivalente da Fase 3, mas a
mesma ideia: só aceitar valores onde o dado é confiável.

### A máscara de água: por que precisa de `.unmask(0)`

```python
def construir_mascara_agua(regiao: ee.Geometry) -> ee.Image:
    occurrence = ee.Image(COLECAO_AGUA).select(BANDA_AGUA).clip(regiao).unmask(0)
    return occurrence.gte(LIMIAR_OCCURRENCE_AGUA)
```

A banda `occurrence` (JRC Global Surface Water) só tem valor onde **já
houve água alguma vez** entre 1984-2021 — em qualquer outro pixel (terra
firme, nunca alagou), ela vem **sem dado nenhum** (mascarada), não com 0.
Se não tratássemos isso, `occurrence.gte(50)` num pixel sem dado devolveria
"sem dado" também (comparação com algo mascarado propaga a máscara), e
esse pixel ficaria de fora tanto da máscara de água quanto, por causa de
como as máscaras se combinam depois, potencialmente do resultado final.
`.unmask(0)` substitui "sem dado" por `0` explicitamente **antes** da
comparação — dizendo "onde o JRC nunca viu água, tratamos como 0% de
ocorrência", que é semanticamente correto (ausência de registro de água
= nunca foi água, não "não sei").

### Escolhendo o limiar de 50: olhando a distribuição real, não chutando

Antes de fixar um número, rodei uma checagem rápida (`ee.Reducer.percentile`
+ `ee.Reducer.fixedHistogram`) da banda `occurrence` sobre o bbox inteiro:

```
Percentis: p1=17.4  p5=60.8  p10=80.7  p25=94.8  p50=98.4  p75=98.4  p90=99.0
Histograma (10 faixas de 0-100): a faixa 90-100 sozinha tem 329.312 "pixels"
(ponderados), contra ~61.500 somados em todas as faixas de 0 a 90.
```

Achado interessante: os percentis parecem "todos altos" à primeira vista,
mas isso é enviesado — a banda só tem valor onde já existiu água alguma
vez, então qualquer estatística sobre ela já está olhando só pro "universo
dos pixels molhados em algum momento", não pro bbox inteiro. Dentro desse
universo, a distribuição é fortemente bimodal: a esmagadora maioria dos
pixels com QUALQUER registro de água está entre 90-100% (o leito
permanente do rio), com uma cauda pequena de pixels "molhados às vezes"
(margens, áreas que alagam sazonalmente) nas faixas mais baixas.

Isso justifica `LIMIAR_OCCURRENCE_AGUA = 50` (em `config.py`): separa bem
"isso é o rio" de "isso é terra que ocasionalmente alaga", sem precisar de
um valor muito mais preciso — o salto de 21.897 (faixa 80-90) pra 329.312
(faixa 90-100) mostra que o corte não é sensível a estar exatamente em 50
vs. 60 vs. 70; qualquer valor nessa faixa separaria os mesmos dois grupos.

### Armadilha real: `reduceRegions` nomeia a coluna diferente pra 1 banda vs. várias

A validação (abaixo) começou devolvendo "sem célula/dado aqui" pros 7
pontos de referência — nenhum erro, só `None` silencioso em todo mundo.
Depurando de fora pra dentro (primeiro confirmando que o ponto cai dentro
do bbox, depois que a grade tem uma célula ali, depois testando o
`reduceRegions` isolado), a causa apareceu:

```python
img = ee.ImageCollection(COLECAO_NDVI)...select("NDVI").mean()
tabela = img.reduceRegions(collection=grade, reducer=ee.Reducer.mean(), scale=250)
tabela.first().toDictionary().getInfo()
# {'mean': 8516.36, 'cell_id': ..., 'lat': ..., 'lon': ...}
#  ^^^^^^ não "NDVI"!
```

Na Fase 3, a imagem reduzida tinha **duas** bandas (`LST_Day_1km`,
`LST_Night_1km`), e cada uma virou automaticamente uma coluna com o próprio
nome. Aqui, a imagem tem **uma banda só** (`NDVI`) — e nesse caso,
`reduceRegions` nomeia a coluna de saída pelo **redutor** (`"mean"`, o nome
genérico de `ee.Reducer.mean()`), não pela banda. É uma inconsistência real
de comportamento da API entre os dois casos, não um erro de digitação meu.
Meu código pedia `.get("NDVI")` — que sempre devolvia `None`, silenciosamente,
porque a coluna não existia com esse nome.

**Correção:** forçar o nome do redutor:

```python
reducer=ee.Reducer.mean().setOutputs(["NDVI"])
```

`setOutputs([...])` nomeia explicitamente a(s) saída(s) do redutor,
eliminando a dependência do comportamento "adivinhado" do Earth Engine — o
mesmo princípio de "não confiar em convenção implícita" que já apareceu no
adendo da Fase 0 (não confiar no `system:index` pra `cell_id`).

### Validação contra os pontos de referência

```python
for nome, (lat, lon) in PONTOS_REFERENCIA.items():
    ponto = ee.Geometry.Point([lon, lat])
    celula_mais_proxima = tabela_julho_2020.filterBounds(ponto).first()
    ndvi = celula_mais_proxima.get("NDVI").getInfo()
```

Diferente da Fase 3 (que comparou contra um número já calculado na Fase 2),
aqui a validação é contra os `PONTOS_REFERENCIA` do `config.py` — coordenadas
de bairros que a literatura (estudo da UEA) já classificou como ilha de
calor ou controle. `filterBounds(ponto)` encontra a célula da grade que
contém aquele ponto; `.first()` pega essa única célula (a interseção
deveria dar exatamente uma, já que a grade não tem sobreposição).

### Resultado

```
Validação — NDVI em julho/2020 nos pontos de referência:
  reserva_ducke: NDVI = 0.877   (floresta preservada — esperado ~0.85, alto)
  centro:        NDVI = 0.277   (esperado ~0.3 ou menos, baixo)
  aleixo:        NDVI = 0.360   (ilha de calor conhecida, UEA)
  petropolis:    NDVI = 0.303   (ilha de calor conhecida, UEA)
  cidade_nova:   NDVI = 0.420   (ilha de calor conhecida, UEA)
  japiim:        NDVI = 0.311   (ilha de calor conhecida, UEA)
  ponta_negra:   NDVI = 0.724   (controle: urbana mas arborizada — bem mais alta que as outras)
```

Bateu com tudo que se esperava: Reserva Ducke bem acima do resto, Centro
bem abaixo, os quatro bairros de ilha de calor do estudo da UEA todos numa
faixa baixa e parecida entre si, e o controle arborizado nitidamente
destacado dos bairros de ilha de calor — exatamente o padrão que a
literatura já descreveu, reproduzido pelo pipeline sem ter sido "ensinado"
a reproduzir esse padrão especificamente.

**Critério de pronto da Fase 4 (do plano):** ✅ Reserva Ducke ~0,85+,
Centro ~0,3 ou menos — confirmado, com folga.

### Exportação e conferência final

```
Task "mapa_amazonia_ndvi_mensal": SUCCEEDED
Baixado: data/raw/ndvi_mensal_2001_2025.csv
```

```
shape: (612000, 6)
NDVI: 459.752 de 612.000 preenchidas (75%) — nublado/água descartados no resto
NDVI: min -0.1988, média 0.737, máx 0.998
Julho/2020, média do bbox inteiro: 0.7465
```

A média geral (0,74) sai alta porque o bbox tem mais área de floresta
(Reserva Ducke e entorno) do que área urbana — bate com a expectativa: se
desse próximo de 0,3 pra cidade inteira, seria sinal de erro (bbox errado,
ou máscara descartando floresta por engano). O mínimo levemente negativo
(-0,1988) é esperado — sobra alguma margem de rio que passou pela máscara
de água num limiar, ou pixel de baixa qualidade que passou pelo `SummaryQA`.

**Nota sobre o "buraco" de dados na hora de rodar em background:** ao
disparar este script com `run_in_background`, o arquivo de saída ficou
vazio por um tempo mesmo com o processo rodando de verdade — não é bug do
script, é que o Python usa buffer de saída maior quando `stdout` não é um
terminal (é um arquivo, no caso do `run_in_background`). A forma confiável
de checar o progresso nesse caso não foi ler o print do script, foi
consultar a API do Earth Engine direto (`ee.data.listOperations()`), que
não depende de nenhum buffer de output do processo Python.

---

## Fase 5 — Montar as tabelas finais

### Objetivo desta fase

As Fases 3 e 4 baixaram dois CSVs crus, cada um com 612.000 linhas
(2.040 células x 300 meses): um de temperatura (`lst_mensal_2001_2025.csv`),
outro de vegetação (`ndvi_mensal_2001_2025.csv`). Nenhum dos dois é o que o
site vai ler. A Fase 5 (`scripts/05_montar_tabelas.py`) faz a ponte:

1. Junta os dois num só, célula-mês a célula-mês.
2. Limpa valores fisicamente implausíveis.
3. Confere que os números batem com o esperado (`assert`, não "parece bom").
4. Salva 25 arquivos Parquet (um por ano) — o formato que o front-end
   (Fase 6) vai carregar sob demanda.
5. Gera `grade.geojson` — a geometria das 2.040 células, que os CSVs nunca
   guardaram (só o centroide).

Diferente das Fases 3/4, quase todo este script roda em `pandas`, local, sem
esperar nenhuma exportação assíncrona — só a geometria da grade precisa do
Earth Engine de novo.

### Juntando as duas tabelas sem confiar que "vêm da mesma grade" é garantia

```python
def carregar_e_juntar() -> pd.DataFrame:
    lst = pd.read_csv(DIR_RAW / "lst_mensal_2001_2025.csv")
    ndvi = pd.read_csv(DIR_RAW / "ndvi_mensal_2001_2025.csv")

    comparacao = lst.merge(ndvi, on=["cell_id", "ano", "mes"], suffixes=("", "_ndvi"))
    coordenadas_batem = np.allclose(comparacao["lon"], comparacao["lon_ndvi"]) and np.allclose(
        comparacao["lat"], comparacao["lat_ndvi"]
    )
    assert coordenadas_batem, (
        "lon/lat de LST e NDVI divergem para o mesmo cell_id — Fase 3 e Fase 4 "
        "não usaram a mesma grade?"
    )

    ndvi_sem_coordenadas = ndvi.drop(columns=["lon", "lat"])
    tabela = lst.merge(
        ndvi_sem_coordenadas, on=["cell_id", "ano", "mes"], how="outer", indicator=True
    )

    apenas_de_um_lado = tabela[tabela["_merge"] != "both"]
    assert apenas_de_um_lado.empty, (
        f"{len(apenas_de_um_lado)} linhas existem só em LST ou só em NDVI "
        "— Fase 3 e Fase 4 deveriam ter processado exatamente a mesma "
        "grade e o mesmo período."
    )
    tabela = tabela.drop(columns=["_merge"])
    ...
```

Duas decisões que valem a pena entender, não só ler:

- **`how="outer"` + `indicator=True`, não `how="inner"`.** Um `inner` join
  junta só o que casa dos dois lados e descarta o resto **em silêncio** — se
  por algum motivo a Fase 3 tivesse processado um mês a mais que a Fase 4
  (ou uma célula a menos), um `inner` produziria uma tabela menor sem avisar
  nada de errado. Com `outer` + `indicator="_merge"`, toda linha ganha uma
  marca (`"left_only"`, `"right_only"` ou `"both"`) e o `assert` logo depois
  falha alto e explica o motivo, em vez de deixar passar um dado incompleto.
- **Conferir `lon`/`lat` antes de descartar a cópia do NDVI.** Os dois CSVs
  têm `lon`/`lat`, vindos da mesma função `construir_grade()` — na teoria,
  idênticos. Mas "na teoria" já causou dois bugs reais nas Fases 3 e 4 (QC
  do MOD11A2, nome de coluna do `reduceRegions`). Em vez de assumir e
  simplesmente descartar uma das cópias, o script primeiro compara as duas
  com `np.allclose` (tolerância de ponto flutuante) e só descarta depois de
  confirmar. Isso é o mesmo princípio de "não confiar em convenção
  implícita" que já apareceu duas vezes antes neste projeto.

### Faixas plausíveis: transformar erro de sensor em "sem dado", não descartar a linha

```python
def aplicar_faixas_plausiveis(tabela: pd.DataFrame) -> pd.DataFrame:
    faixas = {
        "lst_dia_c": (LST_MIN_C, LST_MAX_C),
        "lst_noite_c": (LST_MIN_C, LST_MAX_C),
        "ndvi": (NDVI_MIN, NDVI_MAX),
    }
    for coluna, (minimo, maximo) in faixas.items():
        fora_da_faixa = ~tabela[coluna].between(minimo, maximo) & tabela[coluna].notna()
        n_fora = int(fora_da_faixa.sum())
        if n_fora:
            print(f"  {coluna}: {n_fora} valor(es) fora de [{minimo}, {maximo}] -> virando nulo")
        tabela.loc[fora_da_faixa, coluna] = np.nan
    return tabela
```

`config.py` já trazia `LST_MIN_C, LST_MAX_C = 10.0, 60.0` e
`NDVI_MIN, NDVI_MAX = -1.0, 1.0` (seção 7, prevista desde a Fase 0 para "as
checagens de sanidade da Fase 5"). A regra: um valor fora da faixa vira
nulo **naquela coluna daquela célula-mês**, não faz a linha inteira
desaparecer — mesma filosofia de "mês nublado = sem dado" já decidida no
`plano.html` para valores ausentes. O site vai mostrar "sem dado" em vez de
inventar um número ou, pior, publicar um número fisicamente impossível.

### Armadilha real: LST negativo em pleno equador

Rodar essa função contra os dados de verdade (não só ler o plano) encontrou
algo que não estava previsto:

```
lst_dia_c: 58 valor(es) fora de [10.0, 60.0] -> virando nulo
lst_noite_c: 30 valor(es) fora de [10.0, 60.0] -> virando nulo
```

Investigando as 58 linhas de `lst_dia_c` antes de simplesmente confiar no
filtro: o pior caso era **-7,49°C** — impossível para superfície em Manaus,
mesmo de noite, mesmo na estação mais fria. Três padrões chamaram atenção:

- Só 0,009% das 612.000 linhas — não é um erro sistemático, é raro.
- Concentradas em pouquíssimos meses específicos (2006-05 sozinho tinha 21
  das 58; 2008-03 tinha 19) — não distribuídas aleatoriamente no tempo.
- Em quase todas, `lst_noite_c` da mesma célula/mês também estava vazio.

A explicação mais provável: nesses meses, a composição mensal daquela
célula teve poucos pixels de 8 dias disponíveis (mês excepcionalmente
nublado), e um dos poucos que sobrou tinha contaminação de nuvem que passou
pelo QC. O QC corrigido na Fase 3 (`.lt(2)`, "aceita flag 0 ou 1") resolveu
o caso de `LST_Night_1km` zerado por inteiro, mas "flag 1 = erro médio
<= 2K" não é uma garantia absoluta de céu limpo, só a melhor garantia que o
produto oferece — com poucas amostras no mês, um único pixel ruim pesa
muito na média. A checagem de faixa plausível da Fase 5 existe exatamente
para pegar esse tipo de sobra que passa pelas máscaras anteriores.

**Conclusão prática:** não foi preciso mudar nada nas Fases 3/4 — o filtro
de faixa plausível da própria Fase 5 já é o mecanismo certo para essa
sobra rara, e vale documentar aqui para não ser confundido com um bug novo
se aparecer de novo em dados futuros.

### Checagens de sanidade e contagem de nulos

```python
def checagens_de_sanidade(tabela: pd.DataFrame) -> None:
    for coluna, (minimo, maximo) in {...}.items():
        valores = tabela[coluna].dropna()
        assert valores.between(minimo, maximo).all(), (...)

    print("Contagem de nulos por coluna (meses nublados / filtrados):")
    for coluna in COLUNAS_LST + [COLUNA_NDVI]:
        n_nulos = int(tabela[coluna].isna().sum())
        pct = 100 * n_nulos / len(tabela)
        print(f"  {coluna}: {n_nulos} ({pct:.1f}%)")
```

Resultado real:

```
lst_dia_c: 41643 (6.8%)
lst_noite_c: 384868 (62.9%)
ndvi: 152248 (24.9%)
```

`lst_noite_c` faltando em 62,9% dos casos é o número mais chamativo, mas é
esperado e não é bug: capturar LST **noturna** exige um pixel sem nuvem
bem à noite, num lugar (Amazônia) onde a nebulosidade já é o obstáculo
técnico nº 1 do projeto — e foi exatamente esse dado que, na Fase 3, quase
saiu 100% vazio antes da correção do QC. 62,9% de meses sem leitura
noturna confiável é plausível para essa região; seria motivo de suspeita se
esse número fosse parecido com o de `lst_dia_c` (6,8%) ou se fosse 100%.

### Particionando por ano

```python
def salvar_parquets_por_ano(tabela: pd.DataFrame) -> None:
    DIR_PROCESSED.mkdir(parents=True, exist_ok=True)
    colunas_finais = ["cell_id", "lon", "lat", "ano", "mes"] + COLUNAS_LST + [COLUNA_NDVI]

    total_salvo = 0
    for ano in range(ANO_INICIO, ANO_FIM + 1):
        fatia = tabela.loc[tabela["ano"] == ano, colunas_finais]
        caminho = DIR_PROCESSED / f"manaus_{ano}.parquet"
        fatia.to_parquet(caminho, index=False)
        total_salvo += len(fatia)

    assert total_salvo == len(tabela), (...)
```

Um Parquet por ano, não um arquivo único de 612.000 linhas: o slider de
tempo da Fase 6 só precisa carregar o(s) ano(s) que estão visíveis num dado
momento — carregar os 25 anos de uma vez seria buscar ~13 MB de dado (25 x
~530 KB) só pra mostrar um mês. Cada arquivo saiu entre ~480 KB e ~570 KB
(~24.480 linhas cada, 2.040 células x 12 meses) — Parquet compactado, contra
um CSV equivalente que seria bem maior (Parquet é binário, tipado e
comprimido; ver nota da Fase 0 sobre isso).

Colunas renomeadas na saída (`LST_Day_1km` -> `lst_dia_c`,
`LST_Night_1km` -> `lst_noite_c`, `NDVI` -> `ndvi`): os nomes internos do
Earth Engine fazem sentido nos scripts de coleta, mas o arquivo final é
"o que o site consome" — vale ter nomes que qualquer pessoa lendo o
front-end entenda sem abrir o `plano.html` pra traduzir.

### Gerando `grade.geojson`

```python
def gerar_grade_geojson(n_celulas_esperado: int) -> None:
    ee.Initialize(project=EE_PROJECT_ID)
    grade = (
        construir_grade()
        .select(["cell_id", "lon", "lat"])
        .map(_reprojetar_para_wgs84)
    )
    geojson = grade.getInfo()
    ...
```

Os CSVs guardam só o centroide (`lon`, `lat`) de cada célula — suficiente
pra fazer o `join` da Fase 5, mas não pra desenhar um polígono no mapa da
Fase 6. `construir_grade()` (o mesmo módulo `grade.py` usado nas Fases 3 e
4) recria a geometria completa; `.getInfo()` traz a coleção inteira pro
Python já em formato GeoJSON, num único request síncrono — viável aqui
porque são só ~2.040 polígonos retangulares simples (bem abaixo de qualquer
limite de payload), diferente das tabelas de 612 mil linhas das Fases 3/4,
que precisaram do fluxo assíncrono `Export.table.toDrive` + polling.

### Armadilha real: a grade saiu em metros, não em graus

Primeira versão do `.getInfo()`, sem reprojeção, produziu isto:

```json
{"type": "Polygon", "coordinates": [[[-6702000, -357000], [-6701000, -357000], ...]],
 "crs": {"type": "name", "properties": {"name": "EPSG:3857"}}}
```

`-6702000` não é uma longitude — é metros em Web Mercator (EPSG:3857), a
projeção que `construir_grade()` usa de propósito pra que "1000 metros"
tenha um significado concreto ao montar a grade (ver Fase 3). O formato
GeoJSON, por especificação (RFC 7946), exige coordenadas em graus, WGS84
(EPSG:4326) — e é isso que o MapLibre GL (Fase 6) espera ao carregar um
`.geojson`. Sem corrigir, o arquivo seria um GeoJSON *sintaticamente*
válido, carregaria sem erro nenhum, e desenharia a grade inteira fora do
mapa (ou em escala absurda) — o tipo de bug que só aparece testando o mapa
de verdade, não lendo o código.

Correção: reprojetar a geometria de cada célula antes de exportar.

```python
def _reprojetar_para_wgs84(celula: ee.Feature) -> ee.Feature:
    geometria_wgs84 = celula.geometry().transform("EPSG:4326", 1)
    return celula.setGeometry(geometria_wgs84)
```

`.transform("EPSG:4326", 1)` converte a geometria pra graus, com tolerância
de 1 metro (`maxError`) — irrelevante numa grade de 1 km. Depois da
correção, a mesma célula:

```json
{"type": "Polygon", "coordinates": [[[-60.205, -3.205], [-60.196, -3.205],
                                       [-60.196, -3.196], [-60.205, -3.196],
                                       [-60.205, -3.205]]]}
```

Coordenadas dentro do bbox de Manaus (`[-60.20, -3.20, -59.75, -2.85]`), como
esperado. Um `assert` foi acrescentado ao script pra travar essa checagem
(coordenada dentro de uma faixa de graus plausível pro bbox) — não só
confiar visualmente de novo se o script for alterado no futuro.

### Resultado

```
lst_dia_c: 58 valor(es) fora de [10.0, 60.0] -> virando nulo
lst_noite_c: 30 valor(es) fora de [10.0, 60.0] -> virando nulo

Contagem de nulos por coluna:
  lst_dia_c: 41643 (6.8%)
  lst_noite_c: 384868 (62.9%)
  ndvi: 152248 (24.9%)

25 arquivos Parquet salvos (612000 linhas no total).
grade.geojson salvo (2040 células).
```

**Critério de pronto da Fase 5 (do plano):** ✅ 25 arquivos Parquet existem,
nenhuma asserção falhou, e o total de linhas bate com o esperado
(2.040 células x 300 meses = 612.000).

### Adendo — segunda rodada de checagem, procurando anomalias específicas de Manaus

As faixas plausíveis do `config.py` (10-60°C) são um limite genérico —
"fisicamente possível em qualquer lugar do planeta". Depois de rodar a Fase
5 pela primeira vez, veio um pedido de olhar mais fundo: existe algo fora
da faixa genérica mas que ainda **não faz sentido especificamente pra
Manaus** (cidade equatorial, quente o ano todo, sem inverno)?

**1) Validação de temperatura contra `PONTOS_REFERENCIA` (nunca tinha sido feita — só o NDVI foi validado na Fase 4):**

```
reserva_ducke   dia=27.94°C  noite=22.09°C  (mais fria — floresta preservada)
centro          dia=33.04°C  noite=25.23°C
aleixo          dia=35.66°C  noite=24.81°C
petropolis      dia=36.73°C  noite=25.01°C  (mais quente — bate com o estudo da UEA)
cidade_nova     dia=35.11°C  noite=24.58°C
japiim          dia=36.60°C  noite=25.06°C
ponta_negra     dia=27.97°C  noite=24.45°C  (controle arborizado — quase tão fria quanto a reserva)
```

Reproduz exatamente o padrão que a literatura já descreveu (mesmo critério
da Fase 4): Reserva Ducke e Ponta Negra (controle arborizado) nitidamente
mais frias, os quatro bairros do estudo da UEA nitidamente mais quentes —
mais uma confirmação de que o pipeline está capturando um sinal real, não
ruído.

**2) Armadilha real encontrada: inversão térmica implausível (noite mais quente que o dia).**

Superfície mais quente à noite que de dia é fisicamente estranho em
qualquer lugar, mas seria absurdo em Manaus especificamente — sol forte o
ano todo, sem estação fria. Comparando `lst_dia_c` e `lst_noite_c` da mesma
célula/mês:

```
4.607 de 214.417 células-mês com os dois valores (2,15%) tinham noite > dia
```

A maioria desses (95%) tinha diferença pequena (< 3°C) — plausível num mês
de chuva muito pesada, que encobre o sol o mês inteiro e reduz a amplitude
térmica dia/noite. Mas 82 casos (0,013% do total) tinham diferença **maior
que 5°C**, chegando a **15,68°C** numa célula em fevereiro/2010 (dia
10,11°C, noite 25,79°C). Isolando esse grupo:

```
lst_dia_c nesse grupo:   10,1 – 25,6°C (mediana 17,9) — bem abaixo do normal da cidade
lst_noite_c nesse grupo: 22,0 – 33,3°C (mediana 24,6) — dentro da faixa normal (5%-95% = 20,2-26,5°C)
```

Ou seja: a leitura **noturna** continuava normal, só a **diurna** estava
fora do lugar — mesma assinatura da armadilha original (resíduo de nuvem
que passa pelo QC em meses muito nublados), só que dessa vez o valor ficava
acima de 10°C (passando pela faixa plausível genérica) mas ainda assim
implausível *para Manaus*, porque nenhum dia de Manaus é 10-15°C mais frio
que a própria noite seguinte.

**Correção:** nova constante `LIMIAR_INVERSAO_NOITE_DIA_C = 5.0` no
`config.py`, e uma função nova no script:

```python
def filtrar_inversao_termica(tabela: pd.DataFrame) -> pd.DataFrame:
    ambos_presentes = tabela["lst_dia_c"].notna() & tabela["lst_noite_c"].notna()
    inversao_grande = ambos_presentes & (
        tabela["lst_noite_c"] - tabela["lst_dia_c"] > LIMIAR_INVERSAO_NOITE_DIA_C
    )
    tabela.loc[inversao_grande, "lst_dia_c"] = np.nan
    return tabela
```

Só `lst_dia_c` vira nulo, não os dois — porque foi só ela que se mostrou
fora do normal dentro do grupo afetado. Rodado de novo, os 25 Parquet
subiram de 41.643 para 41.725 nulos em `lst_dia_c` (+82, exatamente o
esperado); `lst_noite_c` e `ndvi` não mudaram. `checagens_de_sanidade`
ganhou um `assert` companheiro, garantindo que nenhuma inversão grande
sobreviva.

**3) Pico de calor isolado em junho/2001 — hipótese errada, corrigida com dado externo.**

Comparando cada célula com a própria média histórica **no mesmo mês do
calendário** (não mês a mês cru, que confundiria a sazonalidade real de
Manaus com anomalia):

```python
grp = df.groupby(['cell_id', 'mes'])['lst_dia_c']
z = (df['lst_dia_c'] - grp.transform('mean')) / grp.transform('std')
# 430 células-mês com |z| > 4 no total (0,075%); 59 delas caem em junho/2001
```

apareceu um grupo de ~30 células vizinhas, todas em junho/2001, com
`lst_dia_c` entre 38°C e 42,01°C — formando um gradiente espacial suave
(núcleo de 4 células empatadas em 42,01°C, caindo gradualmente até o
normal fora do grupo) que sumia por completo no mês seguinte.

**Primeira hipótese (registrada aqui e depois corrigida): evento real de
calor** — queimada/desmatamento expondo solo quente, já que o formato
(pico concentrado, coerente espacialmente, some no mês seguinte) parecia
o oposto de contaminação por nuvem (que dá frio isolado e sem coerência
espacial), e junho é o início típico da estação seca amazônica.

**Essa hipótese estava errada.** O Bruno pesquisou de forma independente
(fonte externa, não o pipeline) e junho/2001 teve **recorde de frio** em
Manaus — o oposto do que a hipótese do "evento de calor real" previa.
Voltando aos dados com essa pista: junho/2001 teve **0% de leitura
noturna válida em toda a grade** (2.040 de 2.040 células com
`lst_noite_c` nulo — nenhum outro junho em 25 anos chega perto disso) e a
completude diurna caiu pra 86,7% (contra ~100% em todos os outros
junhos). Ou seja: foi um mês excepcionalmente nublado de verdade — bate
com o recorde de frio (friagem: entrada de massa de ar fria que também
traz céu encoberto) — e é justamente em meses assim, com poucos pixels de
satélite sobrando, que os dois lados do erro de composição aparecem: já
tínhamos visto o lado **frio** (item 2 acima, resíduo de nuvem
sub-registrando a temperatura); junho/2001 mostra o lado **quente** do
mesmo problema — os poucos pixels de dia que sobraram numa área
específica vieram de uma fonte de erro diferente da nuvem-fria (possível
neblina/aerossol, ou um artefato do próprio algoritmo do produto rodando
com pouquíssima amostra), não de um evento de superfície real.

**Lição:** um padrão que "parece" consistente com uma explicação
plausível (queimada, sazonalidade) não é prova — history real (uma fonte
externa) bateu de frente com a hipótese. Onde antes eu tinha decidido não
filtrar por medo de cortar sinal real do projeto, agora, com a
completude de dado do mês como evidência corroborante, dá pra filtrar com
confiança.

**Correção aplicada:** nova constante `LIMIAR_Z_CLIMATOLOGICO = 4.0` no
`config.py` e função `filtrar_anomalias_climatologicas()`, chamada depois
do filtro de inversão dia/noite — mesmo `z`-score usado no diagnóstico,
agora rodando dentro do pipeline de verdade:

```python
def filtrar_anomalias_climatologicas(tabela: pd.DataFrame) -> pd.DataFrame:
    for coluna in COLUNAS_LST:
        grupo = tabela.groupby(["cell_id", "mes"])[coluna]
        media = grupo.transform("mean")
        contagem = grupo.transform("count")
        desvio = grupo.transform("std")

        z = (tabela[coluna] - media) / desvio
        anomalo = (
            tabela[coluna].notna() & (contagem >= 10) & (z.abs() > LIMIAR_Z_CLIMATOLOGICO)
        )
        tabela.loc[anomalo, coluna] = np.nan
    return tabela
```

`contagem >= 10`: só confia no desvio-padrão de uma célula-mês (ex.: "toda
célula X em todo junho", até 25 amostras) se houver pelo menos 10 anos com
dado — com menos que isso o desvio-padrão fica instável demais pro `z`
significar algo. Rodando contra os dados reais: **430 valores de
`lst_dia_c`** (incluindo as ~30 células de junho/2001 inteiras) e **6 de
`lst_noite_c`** viraram nulos — o cluster de junho/2001 confirmado zerado
depois da correção (`max(lst_dia_c)` em junho/2001 caiu de 42,01°C pra
34,01°C, o novo máximo vindo de uma célula fora do cluster suspeito).

Diferente da faixa plausível e da inversão dia/noite (impossibilidades
físicas universais), este filtro é estatístico e específico de cada
célula — por isso o limiar de 4 desvios-padrão e a exigência de pelo menos
10 anos de histórico, pra não confundir variação sazonal real com erro.

### Registro de todos os critérios de limpeza, num lugar só

A pedido do Bruno, todo critério de limpeza acima (faixa plausível,
inversão térmica, anomalia climatológica — e a deriva orbital, abaixo)
agora também vive em `data/processed/criterios_limpeza.json`, num formato
que a Fase 6 pode consumir direto (cada critério com coluna afetada,
motivo, quantidade de linhas afetadas e status). Pensado como a "página de
metodologia" do site, não só um registro interno. Também criei
`data/processed/eventos_anomalias.json` com os eventos climáticos reais
(secas, cheias, friagem) e as fontes usadas pra confirmar cada um — pra
citar ao lado de um pico/vale no gráfico.

---

## Fase 5b — Deriva orbital do Terra: medir e (tentar) corrigir

### Confirmando com dado do próprio satélite

O double-check anterior levantou a hipótese, por pesquisa externa, de que o
resfriamento de 2025 seria a deriva orbital do Terra (documentada pela
NASA), não um evento climático. Em vez de ficar só na coincidência de
datas, `scripts/06_deriva_orbital.py` mediu isso direto: o MOD11A2 (mesmo
produto da Fase 3) já vem com uma banda `Day_view_time`/`Night_view_time` —
o horário local em que cada pixel foi medido — que nunca tínhamos lido.

```python
def horario_medio_do_mes(data_inicio: ee.Date, regiao: ee.Geometry) -> ee.Feature:
    data_fim = data_inicio.advance(1, "month")
    colecao_do_mes = (
        ee.ImageCollection(COLECAO_LST).filterDate(data_inicio, data_fim).filterBounds(regiao)
    )
    hora_dia = (
        colecao_do_mes.map(lambda img: _mascarar_por_qc(img, "Day_view_time", "QC_Day"))
        .mean().multiply(ESCALA_HORA).rename("hora_dia")
    )
    hora_noite = (
        colecao_do_mes.map(lambda img: _mascarar_por_qc(img, "Night_view_time", "QC_Night"))
        .mean().multiply(ESCALA_HORA).rename("hora_noite")
    )
    valores = ee.Image.cat([hora_dia, hora_noite]).reduceRegion(
        reducer=ee.Reducer.mean(), geometry=regiao, scale=1000, maxPixels=1e9
    )
    return ee.Feature(None, valores).set({"ano": data_inicio.get("year"), "mes": data_inicio.get("month")})
```

Diferente das Fases 3/4, é `reduceRegion` (não `reduceRegions`) — só um
número por mês pro bbox inteiro, não uma linha por célula — e por isso os
300 meses cabem num `.getInfo()` síncrono só, sem exportação pro Drive.

**Resultado — hora média de passagem diurna, por ano:**

```
2001-2020: oscila entre 10,39h e 10,52h (media 10,47h, desvio de só 0,11h = ~7 min)
2021: 10,375   2022: 10,281   2023: 10,055   2024: 9,766   2025: 9,311
```

Bate exatamente com a curva que a NASA documenta: estável perto de 10h30
até 2020, e depois caindo — 9h19 em 2025, indo pra 8h30 até o fim da
missão (2026). A passagem noturna também derivou, por uma magnitude
parecida (22,71h em 2001 -> 21,33h em 2025) — mesmo satélite, mesma órbita.

Isso já é uma confirmação sólida, com dado direto do instrumento, não mais
uma hipótese por coincidência de formato.

### Tentando quantificar: quantos °C por hora de passagem?

A ideia do Bruno: se ~90% das medições históricas caem perto de um horário
"de referência" (aqui, ~10h28 em 2001-2020), dá pra usar os ~10% que
aconteceram em horários diferentes pra estimar, com dado real, quanto a
superfície esquenta por hora — e usar isso pra "devolver" aos meses
afetados pela deriva o quanto eles esfriaram só por causa do horário.

Tentativa: regressão linear usando **só o período de referência**
(2001-2020, antes da deriva começar) — importante isolar esse período
porque depois de 2020 o horário de passagem e o ano caminham junto
(colineares), e não dava pra distinguir "efeito do horário" de "tendência
real de longo prazo" se usasse o período todo.

```python
X = [intercepto, hora_dia, dummy_mes_2, ..., dummy_mes_12]  # dummies de mês pra sazonalidade
beta, *_ = np.linalg.lstsq(X, lst_dia_media, rcond=None)
```

**Resultado:**

```
n = 240 meses (2001-2020)
R² = 0,665 (quase todo explicado pelas dummies de mês, i.e. a sazonalidade real de Manaus)
beta_hora_dia = -0,543 °C/hora   erro padrão = 0,533   t = -1,02
IC 95%: -1,587 a +0,501  (inclui zero)
```

**O sinal bate com a física** (passar mais cedo = mais frio), mas o
resultado **não é estatisticamente significativo** — o intervalo de
confiança inclui zero, e até valores positivos. Causa raiz: dentro de
2001-2020 o horário de passagem quase não varia (desvio-padrão de só ~7
minutos) — não tem variação natural suficiente pra "enxergar" o efeito com
confiança nos dados de LST, que têm ruído real (tempo, nuvem residual) bem
maior que esse sinal de 7 minutos.

Busquei também na literatura científica um valor de referência pra taxa de
aquecimento diurno de superfície tropical: o achado mais concreto foi que
floresta tropical tem amplitude diurna **total** (do mínimo ao máximo do
dia) menor que 5°C — mas isso não separa quanto disso é especificamente a
subida das 9h-11h (provavelmente a fase mais rápida do ciclo, não a média
do dia todo), e o bbox de Manaus mistura floresta (baixa amplitude) com
área urbana (amplitude bem maior). Não achei um número pronto e citável
específico o suficiente pra usar como correção.

### Segunda tentativa: usar a curva horária real, não a variação natural do LST

A ideia da regressão acima falhou porque a variação natural do horário de
passagem (2001-2020) é pequena demais (~7 min de desvio-padrão) pra
"aparecer" no meio do ruído da LST mensal. O Bruno sugeriu uma saída: em
vez de tentar extrair a taxa de aquecimento **de dentro da própria LST**,
usar uma fonte que já tem temperatura por hora de verdade — e notou algo
importante: a curva de aquecimento matinal não é linear (a subida das 9h
pras 10h é bem mais íngreme que das 14h pras 15h, perto do pico do dia) —
então a correção precisa vir de uma curva real, não de uma taxa única.

**Fonte:** Open-Meteo Archive API — a mesma da Fase 1, sem chave, sem
custo — mas agora pedindo `hourly=temperature_2m` em vez de `daily`
(`scripts/07_curva_horaria_ar.py`), 2001-2020 (mesmo período de
referência), no mesmo ponto (`centro`, já usado na Fase 1 e em
`PONTOS_REFERENCIA`).

**Climatologia horária resultante** (temperatura média do ar por hora do
dia, ao longo de 20 anos, ~7.300 observações por hora):

```
 hora  temp_media_c
    8        25.797
    9        26.772   (9h -> 10h: +0,90°C)
   10        27.667
   11        28.409   (10h -> 11h: +0,74°C)
   ...
   14        29.285
   15        29.092   (14h -> 15h: -0,19°C — já passou do pico)
```

Confirma exatamente a intuição: perto das 9h-10h (onde a deriva do Terra
está empurrando o horário de passagem) a curva sobe rápido; perto das
14h-15h ela já achatou. Usar uma taxa única (como a regressão tentou) teria
sido uma simplificação grande demais bem no trecho da curva que mais
importa.

### Calibrando a amplitude: LST não é temperatura do ar

A curva acima é do **ar** (2 m), não da **superfície** (LST) — são coisas
diferentes por definição no projeto (aviso já previsto pra Fase 6). Usar a
curva do ar direto como correção da LST subestimaria o efeito: superfície
esquenta e esfria de forma mais extrema que o ar acima dela.

Solução: calibrar um fator de amplificação com os dois horários que a
própria LST já tem — dia (~10h28) e noite (~22h31), na média 2001-2020:

```python
k = (lst_dia_ref - lst_noite_ref) / (ar_dia_ref - ar_noite_ref)
# lst_dia_ref = 28,740°C   lst_noite_ref = 23,081°C
# ar_dia_ref  = 28,013°C   ar_noite_ref  = 25,600°C
# k = 5,659 / 2,413 = 2,3445
```

`k = 2,34` significa que a superfície em Manaus varia ~2,34x mais que o ar
2 m acima dela — plausível (é um resultado bem documentado na
sensoriamento remoto que LST tem amplitude diurna maior que a temperatura
do ar) e, mais importante, **específico de Manaus**, calibrado com os
próprios dados do projeto, não emprestado de uma tabela genérica.

### A correção final

```python
correcao_dia(mes) = k * (temp_ar(hora_dia_referencia) - temp_ar(hora_dia_observada_no_mes))
lst_dia_c_corrigido = lst_dia_c + correcao_dia(mes)
```

(`temp_ar(...)` interpola a climatologia horária em qualquer hora
fracionária, ex.: 9,31h — `np.interp` entre os dois pontos inteiros mais
próximos.) Mesma fórmula pra `lst_noite_c_corrigido`, com a hora de
referência noturna.

`scripts/08_corrigir_deriva_orbital.py` aplica isso aos 25 Parquet,
**sem apagar as colunas originais** — `lst_dia_c`/`lst_noite_c` continuam
existindo do lado de `lst_dia_c_corrigido`/`lst_noite_c_corrigido`, pra
Fase 6 poder alternar entre os dois.

**Correção média por ano** (°C, `corrigido - bruto`):

```
lst_dia_c:                              lst_noite_c:
2001-2020: entre -0,25 e +0,16 (~0)     2001-2020: entre -0,07 e +0,10 (~0)
2021: +0,16    2022: +0,32              2021: -0,03    2022: -0,07
2023: +0,73    2024: +1,30              2023: -0,26    2024: -0,38
2025: +2,26                             2025: -0,74
```

Dois sinais de que o método está fisicamente coerente:

1. **No próprio período de referência (2001-2020), a correção fica perto
   de zero** — esperado, já que ali a hora observada já é perto da hora de
   referência por definição. Isso está travado num `assert` no script (a
   correção média absoluta no período de referência precisa ser < 1°C).
2. **`lst_dia_c` recebe correção positiva, `lst_noite_c` recebe negativa**
   — e isso não foi imposto no código, saiu sozinho da conta. Faz sentido:
   de dia, passar mais cedo mede a superfície antes dela esquentar (precisa
   somar pra compensar); de noite, passar mais cedo mede a superfície mais
   perto do anoitecer, quando ainda não esfriou tanto quanto vai esfriar
   até a hora de referência (precisa subtrair pra compensar).

**Efeito em 2025** (o ano mais afetado): a média anual de `lst_dia_c` era
27,43°C (−2,90 desvios-padrão em relação aos outros 24 anos — o outlier
mais extremo da série). Corrigida, sobe pra 29,69°C (+1,37 desvios-padrão)
— dentro do normal, e coerente com 2025 ainda sendo um ano relativamente
quente, não mais um ano anomalamente frio.

Efeito colateral notável: 2023 e 2024 (anos de seca/El Niño, já
identificados como os mais quentes da série) ficam **ainda mais quentes**
depois da correção (+0,73°C e +1,30°C) — o viés de frio da deriva estava
mascarando parte do sinal real de calor desses anos, não inventando
tendência nova.

### Limitações registradas (não escondidas)

- A correção usa a hora de passagem média do **bbox inteiro** por mês, não
  por célula — assume que a deriva afeta todas as células do mesmo jeito
  no mesmo mês (razoável: é o mesmo satélite sobre uma área pequena em
  poucos minutos de passagem).
- `k` é um fator único (mesmo valor de dia e de noite) porque só há dois
  horários-âncora de LST pra calibrar — não dá pra medir se a amplificação
  superfície/ar muda ao longo do dia com só dois pontos.
- A forma da curva vem do ar, não da superfície (LST não tem dado por hora
  disponível pra calibrar a forma sozinha) — por isso o `k` existe, mas ele
  não elimina 100% a diferença entre os dois fenômenos.

Tudo isso está registrado em `data/processed/criterios_limpeza.json`
(campo `metodologia.limitacoes` da entrada `deriva_orbital_terra`), que
também traz `explicacao_usuario` — o texto em linguagem simples pra
acompanhar o toggle "desligar correção" na Fase 6 (que deve vir **ligado**
por padrão, conforme pedido).

---

<!-- Próxima seção: Fase 6 — Front-end -->
