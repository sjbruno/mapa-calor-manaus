"""
Fase 5b (continuação) — curva horária real de temperatura, pra calibrar a
correção da deriva orbital

A Fase 5b mostrou que não dá pra estimar "quantos °C por hora de passagem"
só com os nossos próprios dados de LST mensal: entre 2001-2020 (antes da
deriva orbital do Terra começar) o horário de passagem quase não varia
(desvio-padrão de só ~7 minutos) — variação pequena demais pra "enxergar"
o efeito no meio do ruído normal de LST.

Ideia do Bruno: usar uma fonte com temperatura por hora de verdade — a
Open-Meteo (mesma API da Fase 1, sem chave, sem custo) tem dado horário
desde 1940. A curva horária de temperatura do ar em Manaus não é linear:
a subida das 9h pras 10h é muito mais íngreme que das 14h pras 15h (perto
do pico do dia, a curva já achatou). Pegando a curva certa, dá pra saber
exatamente quanto ar esquenta entre, digamos, 9h19 (hora de passagem em
2025) e 10h28 (hora de referência 2001-2020) — sem chutar um número da
literatura genérica.

Isso mede TEMPERATURA DO AR (2 m), não temperatura de SUPERFÍCIE (LST) —
são coisas diferentes (ver Fase 6, aviso "LST != temperatura do ar"). Por
isso este script não usa a curva do ar diretamente como correção da LST:
ele usa a curva do ar só pra achar a FORMA (o quanto a temperatura sobe
entre um horário e outro), e calibra a AMPLITUDE com os nossos próprios
dados de LST (ver `calibrar_e_aplicar_correcao()`, no notebook/próximo
script) — o dia e a noite do MOD11A2 já são dois pontos reais de LST em
dois horários conhecidos (~10h28 e ~22h31, na média 2001-2020); a diferença
entre eles, dividida pela diferença correspondente na curva do ar nesses
mesmos dois horários, dá um fator de conversão específico de Manaus.
"""

import requests
import pandas as pd

from mapa_amazonia.config import DIR_PROCESSED

LATITUDE = -3.130
LONGITUDE = -60.023
URL_ARCHIVE_API = "https://archive-api.open-meteo.com/v1/archive"
CAMINHO_PARQUET = DIR_PROCESSED / "curva_horaria_ar.parquet"

# Mesmo período de referência usado pra medir a deriva orbital (Fase 5b) —
# antes da deriva do Terra começar, pra a curva não estar contaminada por
# nenhum efeito de satélite (isso aqui é dado de solo, não teria esse
# problema de qualquer forma, mas usar o mesmo período facilita comparar).
DATA_INICIO = "2001-01-01"
DATA_FIM = "2020-12-31"


def buscar_dados_horarios() -> dict:
    parametros = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "start_date": DATA_INICIO,
        "end_date": DATA_FIM,
        "hourly": "temperature_2m",
        "timezone": "America/Manaus",
    }
    resposta = requests.get(URL_ARCHIVE_API, params=parametros, timeout=180)
    resposta.raise_for_status()
    return resposta.json()


def montar_dataframe(json_bruto: dict) -> pd.DataFrame:
    horario = json_bruto["hourly"]
    df = pd.DataFrame(
        {"data_hora": horario["time"], "temp_ar_c": horario["temperature_2m"]}
    )
    df["data_hora"] = pd.to_datetime(df["data_hora"])
    df["hora"] = df["data_hora"].dt.hour
    df["mes"] = df["data_hora"].dt.month
    return df.dropna(subset=["temp_ar_c"])


def climatologia_por_hora(df: pd.DataFrame) -> pd.DataFrame:
    """
    Média de temperatura do ar por hora do dia (0-23h), ao longo de 20 anos
    — a curva diurna "típica" de Manaus. Também guarda quantas
    observações entraram em cada hora (20 anos x ~365 dias = ~7.300, salvo
    dias sem dado), pra dar confiança de que a média é robusta.
    """
    return (
        df.groupby("hora")
        .agg(temp_media_c=("temp_ar_c", "mean"), n_observacoes=("temp_ar_c", "size"))
        .reset_index()
    )


def main() -> None:
    print(f"Buscando temperatura horária do ar, {DATA_INICIO} a {DATA_FIM}...")
    json_bruto = buscar_dados_horarios()
    df = montar_dataframe(json_bruto)
    print(f"{len(df)} horas baixadas.")

    curva = climatologia_por_hora(df)

    DIR_PROCESSED.mkdir(parents=True, exist_ok=True)
    curva.to_parquet(CAMINHO_PARQUET, index=False)
    print(f"Salvo: {CAMINHO_PARQUET}")
    print()
    print("Climatologia horária (temperatura média do ar, 2001-2020):")
    print(curva.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
