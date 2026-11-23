"""Geracao de relatorios PDF para as analises do Mini DataLab."""

from __future__ import annotations

from io import BytesIO
from typing import Any
from xml.sax.saxutils import escape

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from analytics import analyze_dataframe as analisar


def _texto_pdf(valor: Any, estilo: ParagraphStyle) -> Paragraph:
    texto = str(valor).encode("cp1252", errors="replace").decode("cp1252")
    return Paragraph(escape(texto).replace("\n", "<br/>"), estilo)


def _tabela(linhas: list[list[Any]], largura: float) -> Table:
    estilos = getSampleStyleSheet()
    celulas = [
        [_texto_pdf(valor, estilos["BodyText"]) for valor in linha]
        for linha in linhas
    ]
    quantidade_colunas = len(linhas[0])
    larguras = [largura / quantidade_colunas] * quantidade_colunas
    tabela = Table(celulas, colWidths=larguras, repeatRows=1, hAlign="LEFT")
    tabela.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eef5")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return tabela


def gerar_pdf(dataframe: pd.DataFrame, titulo: str) -> bytes:
    """Gera um PDF com os indicadores da base e devolve seu conteudo em bytes."""
    if not isinstance(titulo, str):
        raise TypeError("titulo deve ser uma string.")

    resultados = analisar(dataframe)
    buffer = BytesIO()
    largura = A4[0] - 36 * mm
    documento = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=titulo,
    )

    estilos = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle(
        "TituloRelatorio",
        parent=estilos["Title"],
        alignment=TA_CENTER,
        spaceAfter=12,
    )
    secao = estilos["Heading2"]
    texto = estilos["BodyText"]
    conteudo = [
        _texto_pdf(titulo, estilo_titulo),
        _texto_pdf("Resumo da base", secao),
        _tabela(
            [
                ["Indicador", "Valor"],
                ["Linhas", resultados["metadata"]["rows"]],
                ["Colunas", resultados["metadata"]["columns"]],
                ["Linhas duplicadas", resultados["duplicate_rows"]],
                ["Memoria estimada (bytes)", resultados["metadata"]["memory_usage_bytes"]],
            ],
            largura,
        ),
        Spacer(1, 4 * mm),
        _texto_pdf("Valores ausentes", secao),
    ]

    ausentes = [["Coluna", "Quantidade", "Percentual"]]
    ausentes.extend(
        [
            [coluna, valores["count"], f'{valores["percentage"]:.2f}%']
            for coluna, valores in resultados["missing_values"].items()
        ]
    )
    conteudo.append(_tabela(ausentes, largura))

    conteudo.extend([Spacer(1, 4 * mm), _texto_pdf("Alertas", secao)])
    if resultados["alerts"]:
        conteudo.extend(
            [_texto_pdf(f'- {alerta["message"]}', texto) for alerta in resultados["alerts"]]
        )
    else:
        conteudo.append(_texto_pdf("Nenhum alerta de qualidade.", texto))

    conteudo.extend(
        [Spacer(1, 4 * mm), _texto_pdf("Estatisticas descritivas", secao)]
    )
    estatisticas = resultados["descriptive_statistics"]
    if estatisticas:
        nomes = list(next(iter(estatisticas.values())))
        linhas = [["Coluna", *nomes]]
        linhas.extend(
            [[coluna, *(valores[nome] for nome in nomes)] for coluna, valores in estatisticas.items()]
        )
        conteudo.append(_tabela(linhas, largura))
    else:
        conteudo.append(_texto_pdf("A base nao possui colunas numericas.", texto))

    conteudo.extend(
        [Spacer(1, 4 * mm), _texto_pdf("Correlacoes fortes", secao)]
    )
    correlacoes = resultados["strong_correlations"]
    if correlacoes:
        linhas = [["Coluna 1", "Coluna 2", "Correlacao"]]
        linhas.extend(
            [[item["column_1"], item["column_2"], item["correlation"]]
             for item in correlacoes]
        )
        conteudo.append(_tabela(linhas, largura))
    else:
        conteudo.append(_texto_pdf("Nenhuma correlacao forte encontrada.", texto))

    conteudo.extend([Spacer(1, 4 * mm), _texto_pdf("Conclusoes", secao)])
    conteudo.extend(
        [_texto_pdf(f"- {item}", texto) for item in resultados["conclusions"]]
    )

    documento.build(conteudo)
    return buffer.getvalue()