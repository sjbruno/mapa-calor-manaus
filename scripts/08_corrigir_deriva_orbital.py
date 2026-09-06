"""
Fase 5b (conclusão) — aplicar a correção de deriva orbital

Junta as duas pontas medidas nesta fase:
  - a hora real de passagem do satélite, por mês (06_deriva_orbital.py);
  - a curva horária real de temperatura do ar em Manaus (07_curva_horaria_ar.py).

Calibra um fator de conversão ar -> superfície com os próprios dados de LST
(dia e noite são dois horários conhecidos, ~10h28 e ~22h31 na média
2001-2020) e usa isso pra projetar cada `lst_dia_c`/`lst_noite_c` pro
horário de referência histórico — sem sobrescrever os valores originais.
`lst_dia_c_corrigido`/`lst_noite_c_corrigido` são colunas novas, lado a
lado com as originais, pra o site poder alternar entre os dois (correção
ligada por padrão, com opção de desligar).

Metodologia completa, com todos os números, em ESTUDO.md (Fase 5b) e em
`data/processed/criterios_limpeza.json` (entrada `deriva_orbital_terra`).
"""

import numpy as np
import pandas as pd

from mapa_amazonia.config import ANO_FIM, ANO_INICIO, DIR_PROCESSED

# Último ano antes da deriva orbital do Terra começar (Fase 5b) — usado
# como "horário de referência" pra corrigir os anos seguintes.
ANO_REFERENCIA_FIM = 2020


def temp_ar_interpolada(curva: pd.DataFrame, hora):
    """Interpola a climatologia horária do ar (24 pontos, um por hora
    inteira) num horário fracionário qualquer (ex.: 9,31h)."""
    return np.interp(hora, curva["hora"], curva["temp_media_c"])


def calcular_correcoes_mensais(
    hora_passagem: pd.DataFrame, curva: pd.DataFrame, k: float, hora_dia_ref: float, hora_noite_ref: float
) -> pd.DataFrame:
    """
    Pra cada um dos 300 meses, quanto `lst_dia_c`/`lst_noite_c` precisa
    mudar pra representar o que teria sido medido no horário de referência,
    em vez do horário real (possivelmente já com deriva) daquele mês.
    """
    df = hora_passagem.copy()
    ar_dia_ref = temp_ar_interpolada(curva, hora_dia_ref)
    ar_noite_ref = temp_ar_interpolada(curva, hora_noite_ref)

    df["correcao_dia"] = k * (ar_dia_ref - temp_ar_interpolada(curva, df["hora_dia"]))
    df["correcao_noite"] = k * (ar_noite_ref - temp_ar_interpolada(curva, df["hora_noite"]))
    return df[["ano", "mes", "correcao_dia", "correcao_noite"]]


def aplicar_e_salvar(correcoes: pd.DataFrame) -> None:
    for ano in range(ANO_INICIO, ANO_FIM + 1):
        caminho = DIR_PROCESSED / f"manaus_{ano}.parquet"
        tabela = pd.read_parquet(caminho)
        n_antes = len(tabela)

        correcoes_do_ano = correcoes.loc[correcoes["ano"] == ano, ["mes", "correcao_dia", "correcao_noite"]]
        tabela = tabela.merge(correcoes_do_ano, on="mes", how="left")
        assert len(tabela) == n_antes, f"{ano}: merge mudou o número de linhas."
        assert tabela["correcao_dia"].notna().all(), f"{ano}: mês sem correção calculada."

        tabela["lst_dia_c_corrigido"] = tabela["lst_dia_c"] + tabela["correcao_dia"]
        tabela["lst_noite_c_corrigido"] = tabela["lst_noite_c"] + tabela["correcao_noite"]
        tabela = tabela.drop(columns=["correcao_dia", "correcao_noite"])

        tabela.to_parquet(caminho, index=False)

    print(f"lst_dia_c_corrigido / lst_noite_c_corrigido adicionadas aos {ANO_FIM - ANO_INICIO + 1} Parquet.")


def main() -> None:
    hora_passagem = pd.read_parquet(DIR_PROCESSED / "hora_passagem_mensal.parquet")
    curva = pd.read_parquet(DIR_PROCESSED / "curva_horaria_ar.parquet").sort_values("hora")
    assert len(hora_passagem) == (ANO_FIM - ANO_INICIO + 1) * 12

    anos_ref = range(ANO_INICIO, ANO_REFERENCIA_FIM + 1)
    dados_ref = pd.concat(
        [pd.read_parquet(DIR_PROCESSED / f"manaus_{a}.parquet") for a in anos_ref], ignore_index=True
    )

    hora_ref = hora_passagem[hora_passagem["ano"] <= ANO_REFERENCIA_FIM]
    hora_dia_ref = hora_ref["hora_dia"].mean()
    hora_noite_ref = hora_ref["hora_noite"].mean()

    ar_dia_ref = temp_ar_interpolada(curva, hora_dia_ref)
    ar_noite_ref = temp_ar_interpolada(curva, hora_noite_ref)

    lst_dia_ref = dados_ref["lst_dia_c"].mean()
    lst_noite_ref = dados_ref["lst_noite_c"].mean()

    # Fator de amplificação superfície/ar: quanto a LST varia pra cada grau
    # que o ar varia, calibrado pelos dois horários reais e conhecidos que
    # já temos (dia e noite), não por um número da literatura genérica.
    k = (lst_dia_ref - lst_noite_ref) / (ar_dia_ref - ar_noite_ref)

    print(f"hora_dia_ref = {hora_dia_ref:.3f}h   hora_noite_ref = {hora_noite_ref:.3f}h")
    print(f"ar_dia_ref = {ar_dia_ref:.3f}°C   ar_noite_ref = {ar_noite_ref:.3f}°C")
    print(f"lst_dia_ref = {lst_dia_ref:.3f}°C   lst_noite_ref = {lst_noite_ref:.3f}°C")
    print(f"k (amplificação superfície/ar) = {k:.4f}")

    correcoes = calcular_correcoes_mensais(hora_passagem, curva, k, hora_dia_ref, hora_noite_ref)

    correcao_media_ref = correcoes.loc[correcoes["ano"] <= ANO_REFERENCIA_FIM, "correcao_dia"].abs().mean()
    assert correcao_media_ref < 1.0, (
        f"Correção média no próprio período de referência é {correcao_media_ref:.2f}°C — "
        "esperava perto de zero (o período de referência não deveria precisar de correção "
        "significativa em si mesmo)."
    )

    print()
    print("Correção média de lst_dia_c por ano (lst_dia_c_corrigido - lst_dia_c):")
    print(correcoes.groupby("ano")["correcao_dia"].mean().round(3).to_string())
    print()
    print("Correção média de lst_noite_c por ano (lst_noite_c_corrigido - lst_noite_c):")
    print(correcoes.groupby("ano")["correcao_noite"].mean().round(3).to_string())

    aplicar_e_salvar(correcoes)


if __name__ == "__main__":
    main()
