"""Interface Streamlit do Mini DataLab."""

from __future__ import annotations

from itertools import combinations

import pandas as pd
import plotly.express as px
import streamlit as st

from analytics import analyze_dataframe, interpret_chart


def _example_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "idade": [22, 35, 29, 41, 22, 35, 29],
            "gasto_mensal": [1200, 2450, 1800, 3100, 1200, 2450, 1800],
            "categoria": [
                "Essencial",
                "Lazer",
                "Essencial",
                "Lazer",
                "Essencial",
                "Lazer",
                "Essencial",
            ],
            "regiao": ["Norte", "Sul", None, "Sudeste", "Norte", "Sul", None],
        }
    )


def _show_analysis(dataframe: pd.DataFrame) -> None:
    results = analyze_dataframe(dataframe)
    metadata = results["metadata"]

    metric_columns = st.columns(4)
    metric_columns[0].metric("Linhas", metadata["rows"])
    metric_columns[1].metric("Colunas", metadata["columns"])
    metric_columns[2].metric("Duplicidades", results["duplicate_rows"])
    missing_total = sum(
        item["count"] for item in results["missing_values"].values()
    )
    metric_columns[3].metric("Valores ausentes", missing_total)

    with st.expander("Metadados e tipos", expanded=False):
        st.write(f"Memoria estimada: {metadata['memory_usage_bytes']:,} bytes")
        st.dataframe(
            pd.DataFrame(
                {
                    "Coluna": metadata["column_names"],
                    "Tipo": [metadata["dtypes"][name] for name in metadata["column_names"]],
                }
            ),
            hide_index=True,
            use_container_width=True,
        )

    st.subheader("Alertas de qualidade")
    if results["alerts"]:
        for alert in results["alerts"]:
            st.warning(alert["message"])
    else:
        st.success("Nenhuma duplicidade ou valor ausente foi encontrado.")

    st.subheader("Estatisticas descritivas")
    statistics = results["descriptive_statistics"]
    if statistics:
        st.dataframe(
            pd.DataFrame.from_dict(statistics, orient="index").rename_axis("Coluna"),
            use_container_width=True,
        )
    else:
        st.info("A base nao possui colunas numericas.")

    st.subheader("Correlacoes fortes")
    correlations = results["strong_correlations"]
    if correlations:
        st.dataframe(pd.DataFrame(correlations), hide_index=True, use_container_width=True)
    else:
        st.info("Nenhuma correlacao atingiu o limite de 0,70.")

    st.subheader("Conclusoes")
    for conclusion in results["conclusions"]:
        st.markdown(f"- {conclusion}")

    st.divider()
    st.subheader("Graficos e interpretacao")
    chart_type = st.selectbox(
        "Tipo de grafico",
        [
            "Frequencia (barras)",
            "Proporcao (pizza)",
            "Distribuicao (histograma)",
            "Relacao entre numericas (dispersao)",
        ],
    )
    numeric_columns = metadata["numeric_columns"]

    if chart_type in {"Frequencia (barras)", "Proporcao (pizza)"}:
        if not metadata["column_names"]:
            st.info("Adicione colunas para criar um grafico.")
            return
        selected_column = st.selectbox("Coluna categorica", metadata["column_names"])
        counts = (
            dataframe[selected_column]
            .dropna()
            .astype(str)
            .value_counts()
            .rename_axis(selected_column)
            .reset_index(name="Frequencia")
        )
        if counts.empty:
            st.info("A coluna selecionada nao possui valores para exibir.")
        elif chart_type == "Frequencia (barras)":
            st.plotly_chart(
                px.bar(counts, x=selected_column, y="Frequencia", title="Frequencia por categoria"),
                use_container_width=True,
            )
        else:
            st.plotly_chart(
                px.pie(counts, names=selected_column, values="Frequencia", title="Proporcao por categoria"),
                use_container_width=True,
            )
        st.info(interpret_chart("barras" if "barras" in chart_type else "pizza", dataframe, x=selected_column))
    elif chart_type == "Distribuicao (histograma)":
        if not numeric_columns:
            st.info("A base nao possui colunas numericas para o histograma.")
            return
        selected_column = st.selectbox("Coluna numerica", numeric_columns)
        st.plotly_chart(
            px.histogram(dataframe, x=selected_column, title=f"Distribuicao de {selected_column}"),
            use_container_width=True,
        )
        st.info(interpret_chart("histograma", dataframe, x=selected_column))
    else:
        pairs = list(combinations(numeric_columns, 2))
        if not pairs:
            st.info("Sao necessarias duas colunas numericas para a dispersao.")
            return
        selected_pair = st.selectbox(
            "Par de colunas",
            pairs,
            format_func=lambda pair: f"{pair[0]} x {pair[1]}",
        )
        x_column, y_column = selected_pair
        st.plotly_chart(
            px.scatter(
                dataframe,
                x=x_column,
                y=y_column,
                title=f"{x_column} x {y_column}",
            ),
            use_container_width=True,
        )
        st.info(interpret_chart("dispersao", dataframe, x=x_column, y=y_column))


def main() -> None:
    st.set_page_config(page_title="Mini DataLab", page_icon="📊", layout="wide")
    st.title("Mini DataLab")
    st.write(
        "Explore um arquivo CSV, identifique problemas de qualidade e veja "
        "estatisticas e interpretacoes automaticas."
    )

    source = st.sidebar.radio("Origem dos dados", ["Enviar CSV", "Usar exemplo"])
    dataframe: pd.DataFrame | None = None
    if source == "Usar exemplo":
        dataframe = _example_dataframe()
    else:
        uploaded_file = st.sidebar.file_uploader("Selecione um arquivo CSV", type=["csv"])
        if uploaded_file is None:
            st.info("Envie um arquivo CSV ou selecione a base de exemplo na barra lateral.")
            return
        try:
            dataframe = pd.read_csv(uploaded_file, sep=None, engine="python")
        except (UnicodeDecodeError, pd.errors.EmptyDataError, pd.errors.ParserError) as error:
            st.error(f"Nao foi possivel ler o CSV: {error}")
            return

    st.subheader("Previa dos dados")
    st.dataframe(dataframe.head(100), use_container_width=True)
    _show_analysis(dataframe)


if __name__ == "__main__":
    main()
