"""
Série histórica de temperatura do ar em Manaus (Open-Meteo).

Constrói a série diária/mensal/anual da temperatura do ar em Manaus desde
1940, sem depender do Earth Engine. Serve como "termômetro geral da cidade"
para contextualizar e validar as camadas de satélite (que são espacialmente
granulares, mas cobrem só 2001-2025).

Fonte: Open-Meteo Archive API (reanálise ERA5) — gratuita, sem chave de
acesso, com dados diários desde 1940.
https://open-meteo.com/en/docs/historical-weather-api

Este script é incremental: se `manaus_ar.parquet` já existe, busca só os dias
posteriores ao último salvo, em vez de rebaixar 1940 inteiro de novo.
"""

import requests
import pandas as pd
import matplotlib.pyplot as plt

from mapa_amazonia.config import DIR_PROCESSED

# Coordenada de referência: o ponto "centro" já definido em
# config.PONTOS_REFERENCIA, para usar a mesma referência em todo o projeto.
LATITUDE = -3.130
LONGITUDE = -60.023

URL_ARCHIVE_API = "https://archive-api.open-meteo.com/v1/archive"
CAMINHO_PARQUET = DIR_PROCESSED / "manaus_ar.parquet"

# Primeiro dia disponível na Open-Meteo Archive API (reanálise ERA5).
INICIO_HISTORICO = "1940-01-01"


def carregar_dados_existentes() -> pd.DataFrame | None:
    """
    Lê o Parquet salvo em execuções anteriores, se existir.

    Devolve None quando é a primeira vez que o script roda (nada em disco
    ainda) — o chamador trata esse caso buscando o histórico completo.
    """
    if CAMINHO_PARQUET.exists():
        return pd.read_parquet(CAMINHO_PARQUET)
    return None


def buscar_dados_diarios(data_inicio: str, data_fim: str) -> dict:
    """
    Chama a Open-Meteo Archive API para o intervalo [data_inicio, data_fim]
    e devolve o JSON bruto da resposta.

    A API não pede chave nem cadastro: é só um GET com parâmetros na URL.
    `requests.get(url, params=...)` monta a query string sozinho (ex.:
    ?latitude=-3.13&longitude=-60.023&...) — não precisamos concatenar texto
    manualmente.
    """
    parametros = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "start_date": data_inicio,
        "end_date": data_fim,
        "daily": "temperature_2m_mean",
        "timezone": "America/Manaus",
    }
    resposta = requests.get(URL_ARCHIVE_API, params=parametros, timeout=60)
    # Se a API devolver erro (4xx/5xx), isso levanta uma exceção aqui mesmo,
    # em vez de deixar o programa seguir com dados que não existem.
    resposta.raise_for_status()
    return resposta.json()


def montar_dataframe(json_bruto: dict) -> pd.DataFrame:
    """
    Converte o bloco "daily" do JSON da Open-Meteo num DataFrame de duas
    colunas: data e temperatura média do dia.

    O JSON vem no formato "colunar" (uma lista por variável, todas do mesmo
    tamanho e alinhadas por posição), não uma lista de dicionários por dia.
    É por isso que a conversão é `pd.DataFrame({"coluna": lista, ...})` e não
    `pd.DataFrame(lista_de_dicts)`.
    """
    diario = json_bruto["daily"]
    df = pd.DataFrame({
        "data": diario["time"],
        "temp_media_c": diario["temperature_2m_mean"],
    })
    # A API devolve datas como texto ("2001-03-15"). Sem converter para
    # datetime de verdade, `resample()` (usado a seguir) não funciona — ele
    # precisa saber que "2001-03-15" vem antes de "2001-03-16", não comparar
    # como texto.
    df["data"] = pd.to_datetime(df["data"])
    return df


def atualizar_serie(existente: pd.DataFrame | None) -> pd.DataFrame:
    """
    Decide o intervalo a buscar e devolve a série diária completa e
    atualizada (existente + novo, sem duplicar nem re-baixar o que já temos).

    Três casos:
    - Nada salvo ainda -> busca o histórico inteiro (1940 até hoje).
    - Já salvo, mas desatualizado -> busca só de (último dia salvo + 1) até hoje.
    - Já atualizado (rodou hoje antes) -> não chama a API de novo.
    """
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

    # A reanálise ERA5 tem uma pequena defasagem: os últimos dias antes de
    # "hoje" às vezes ainda não têm valor processado e chegam como nulo
    # (NaN). Descartamos essas linhas incompletas agora — elas serão
    # buscadas de novo (e preenchidas) na próxima vez que o script rodar,
    # quando o dado já estiver disponível.
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


def agregar_mensal_e_anual(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Gera as médias mensal e anual a partir da série diária.

    `resample()` só funciona com a coluna de data como índice do DataFrame
    (por isso o `set_index` antes). "MS" = Month Start, "YS" = Year Start —
    cada grupo mensal/anual vira uma linha só, com a média das linhas diárias
    que caíram dentro dele.
    """
    df_indexado = df.set_index("data")
    mensal = df_indexado.resample("MS").mean()
    anual = df_indexado.resample("YS").mean()
    return mensal, anual


def salvar_parquet(df_diario: pd.DataFrame) -> None:
    """
    Salva a série diária em Parquet — o formato de armazenamento decidido
    para o projeto inteiro (mais compacto que CSV e preserva o tipo de cada
    coluna, em vez de guardar tudo como texto).

    Só a série diária é salva em disco: mensal e anual são baratas de
    recalcular a partir dela com `resample()`, então não precisam de arquivo
    próprio.
    """
    DIR_PROCESSED.mkdir(parents=True, exist_ok=True)
    df_diario.to_parquet(CAMINHO_PARQUET)
    print(f"Salvo: {CAMINHO_PARQUET}")


def gerar_grafico(anual: pd.DataFrame) -> None:
    """
    Gera um PNG da série anual. É a checagem visual de sanidade: se a linha
    estiver serrilhada de forma estranha ou plana, algo no processamento
    anterior está errado.
    """
    fig, eixo = plt.subplots(figsize=(10, 5))
    eixo.plot(anual.index.year, anual["temp_media_c"], marker="o", markersize=3)
    eixo.set_title("Manaus — temperatura média do ar, por ano (1940–presente)")
    eixo.set_xlabel("Ano")
    eixo.set_ylabel("Temperatura média (°C)")
    eixo.grid(alpha=0.3)
    fig.tight_layout()

    caminho = DIR_PROCESSED / "manaus_ar_anual.png"
    fig.savefig(caminho, dpi=150)
    print(f"Salvo: {caminho}")


def main() -> None:
    existente = carregar_dados_existentes()
    df = atualizar_serie(existente)

    mensal, anual = agregar_mensal_e_anual(df)

    salvar_parquet(df)
    gerar_grafico(anual)


if __name__ == "__main__":
    main()
