"""Funcoes de perfilamento de dados e interpretacao automatica de graficos."""

from __future__ import annotations

import unicodedata
from typing import Any

import pandas as pd
from pandas.api.types import is_numeric_dtype


def _normalize_label(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip().lower())
    return "".join(character for character in normalized if not unicodedata.combining(character))


def analyze_dataframe(
    dataframe: pd.DataFrame,
    correlation_threshold: float = 0.7,
) -> dict[str, Any]:
    """Analisa estrutura, qualidade e relacoes numericas de um DataFrame."""
    if not isinstance(dataframe, pd.DataFrame):
        raise TypeError("dataframe deve ser uma instancia de pandas.DataFrame.")
    if not 0 <= correlation_threshold <= 1:
        raise ValueError("correlation_threshold deve estar entre 0 e 1.")

    row_count, column_count = dataframe.shape
    numeric_columns = [
        str(column)
        for column in dataframe.columns
        if is_numeric_dtype(dataframe[column].dtype)
    ]
    duplicate_count = int(dataframe.duplicated().sum())
    missing_values = {
        str(column): {
            "count": int(dataframe[column].isna().sum()),
            "percentage": (
                round(float(dataframe[column].isna().mean() * 100), 2)
                if row_count
                else 0.0
            ),
        }
        for column in dataframe.columns
    }

    descriptive_statistics: dict[str, dict[str, Any]] = {}
    if numeric_columns:
        descriptions = dataframe[numeric_columns].describe().T
        for column, values in descriptions.iterrows():
            descriptive_statistics[str(column)] = {
                str(statistic): (
                    value.item() if hasattr(value, "item") else value
                )
                for statistic, value in values.items()
            }

    strong_correlations: list[dict[str, Any]] = []
    if len(numeric_columns) >= 2:
        correlation_matrix = dataframe[numeric_columns].corr()
        for left_index, left_column in enumerate(numeric_columns):
            for right_column in numeric_columns[left_index + 1 :]:
                coefficient = correlation_matrix.loc[left_column, right_column]
                if pd.notna(coefficient) and abs(coefficient) >= correlation_threshold:
                    strong_correlations.append(
                        {
                            "column_1": left_column,
                            "column_2": right_column,
                            "correlation": round(float(coefficient), 3),
                        }
                    )
        strong_correlations.sort(
            key=lambda item: abs(item["correlation"]),
            reverse=True,
        )

    alerts: list[dict[str, str]] = []
    if duplicate_count:
        alerts.append(
            {
                "level": "warning",
                "message": (
                    f"Foram encontradas {duplicate_count} linha(s) duplicada(s) "
                    f"({duplicate_count / row_count:.1%} das linhas)."
                ),
            }
        )
    for column, values in missing_values.items():
        if values["count"]:
            alerts.append(
                {
                    "level": "warning",
                    "message": (
                        f"A coluna '{column}' tem {values['count']} valor(es) "
                        f"ausente(s) ({values['percentage']:.2f}%)."
                    ),
                }
            )

    conclusions = [
        f"A base possui {row_count} linha(s) e {column_count} coluna(s)."
    ]
    if duplicate_count:
        conclusions.append(
            f"Ha {duplicate_count} linha(s) duplicada(s) que podem ser revisadas."
        )
    else:
        conclusions.append("Nenhuma linha duplicada foi encontrada.")

    columns_with_missing_values = [
        column for column, values in missing_values.items() if values["count"]
    ]
    if columns_with_missing_values:
        conclusions.append(
            "Valores ausentes encontrados em: "
            + ", ".join(columns_with_missing_values)
            + "."
        )
    else:
        conclusions.append("Nenhum valor ausente foi encontrado.")

    if numeric_columns:
        conclusions.append(
            f"{len(numeric_columns)} coluna(s) numerica(s) possuem estatisticas descritivas."
        )
    else:
        conclusions.append("A base nao possui colunas numericas para descrever.")

    if strong_correlations:
        strongest = strong_correlations[0]
        conclusions.append(
            f"A correlacao mais forte e entre '{strongest['column_1']}' e "
            f"'{strongest['column_2']}' ({strongest['correlation']:.3f})."
        )
    elif len(numeric_columns) >= 2:
        conclusions.append(
            "Nenhuma correlacao atingiu o limite de "
            f"{correlation_threshold:.0%}."
        )
    elif numeric_columns:
        conclusions.append(
            "Sao necessarias ao menos duas colunas numericas para comparar correlacoes."
        )

    metadata = {
        "rows": int(row_count),
        "columns": int(column_count),
        "column_names": [str(column) for column in dataframe.columns],
        "dtypes": {
            str(column): str(dataframe[column].dtype)
            for column in dataframe.columns
        },
        "numeric_columns": numeric_columns,
        "memory_usage_bytes": int(dataframe.memory_usage(deep=True).sum()),
    }

    return {
        "metadata": metadata,
        "missing_values": missing_values,
        "duplicate_rows": duplicate_count,
        "alerts": alerts,
        "descriptive_statistics": descriptive_statistics,
        "strong_correlations": strong_correlations,
        "conclusions": conclusions,
    }


def interpret_chart(
    chart_type: str,
    dataframe: pd.DataFrame,
    x: str | None = None,
    y: str | None = None,
) -> str:
    """Gera uma explicacao curta para graficos categoricos e numericos."""
    if not isinstance(dataframe, pd.DataFrame):
        raise TypeError("dataframe deve ser uma instancia de pandas.DataFrame.")
    if not isinstance(chart_type, str):
        raise TypeError("chart_type deve ser uma string.")
    if dataframe.empty:
        return "Nao ha dados suficientes para interpretar este grafico."

    normalized_type = _normalize_label(chart_type).replace(" ", "_")
    if x is not None and x not in dataframe.columns:
        raise ValueError(f"A coluna '{x}' nao existe no DataFrame.")
    if y is not None and y not in dataframe.columns:
        raise ValueError(f"A coluna '{y}' nao existe no DataFrame.")

    categorical_types = {"pizza", "pie", "barra", "barras", "bar"}
    histogram_types = {"histograma", "histogram", "hist"}
    cross_types = {
        "dispersao",
        "scatter",
        "cruzamento",
        "series_numericas_cruzadas",
        "numeric_cross",
    }

    if normalized_type in categorical_types:
        if x is None:
            return "Selecione uma coluna para analisar as frequencias."
        counts = dataframe[x].dropna().astype(str).value_counts()
        if counts.empty:
            return f"A coluna '{x}' nao possui valores para comparar."
        top_category = str(counts.index[0])
        top_percentage = float(counts.iloc[0] / counts.sum() * 100)
        return (
            f"'{top_category}' e a categoria mais frequente em '{x}', com "
            f"{int(counts.iloc[0])} ocorrencia(s) ({top_percentage:.1f}% dos "
            f"{int(counts.sum())} valores nao ausentes)."
        )

    if normalized_type in histogram_types:
        candidates = [column for column in (x, y) if column is not None]
        numeric_column = next(
            (
                column
                for column in candidates
                if is_numeric_dtype(dataframe[column].dtype)
            ),
            None,
        )
        if numeric_column is None:
            numeric_column = next(
                (
                    str(column)
                    for column in dataframe.columns
                    if is_numeric_dtype(dataframe[column].dtype)
                ),
                None,
            )
        if numeric_column is None:
            return "Nao ha coluna numerica para interpretar o histograma."
        values = dataframe[numeric_column].dropna()
        if values.empty:
            return f"A coluna '{numeric_column}' nao possui valores numericos validos."
        median = float(values.median())
        minimum = float(values.min())
        maximum = float(values.max())
        skew = float(values.skew()) if len(values) > 2 else 0.0
        if abs(skew) < 0.5:
            shape = "aproximadamente simetrica"
        elif skew > 0:
            shape = "assimetrica a direita"
        else:
            shape = "assimetrica a esquerda"
        return (
            f"'{numeric_column}' tem distribuicao {shape}: mediana {median:.3g}, "
            f"minimo {minimum:.3g} e maximo {maximum:.3g} "
            f"({int(values.count())} valor(es) validos)."
        )

    if normalized_type in cross_types:
        if x is None or y is None:
            return "Selecione duas colunas numericas para interpretar a dispersao."
        if not is_numeric_dtype(dataframe[x].dtype) or not is_numeric_dtype(
            dataframe[y].dtype
        ):
            return "A interpretacao de dispersao exige duas colunas numericas."
        paired_values = dataframe[[x, y]].dropna()
        if len(paired_values) < 2:
            return "Sao necessarios ao menos dois pares validos para calcular a correlacao."
        coefficient = paired_values[x].corr(paired_values[y])
        if pd.isna(coefficient):
            return "Nao foi possivel calcular a correlacao (uma coluna pode ser constante)."
        direction = "positiva" if coefficient > 0 else "negativa"
        strength = (
            "forte"
            if abs(coefficient) >= 0.7
            else "moderada"
            if abs(coefficient) >= 0.4
            else "fraca"
        )
        return (
            f"'{x}' e '{y}' apresentam correlacao {direction} {strength} "
            f"(r = {coefficient:.3f}, com {len(paired_values)} pares validos). "
            "Correlacao nao implica causalidade."
        )

    return (
        f"Interpretacao automatica indisponivel para '{chart_type}'. "
        f"A base possui {len(dataframe)} linha(s) e {len(dataframe.columns)} coluna(s)."
    )
