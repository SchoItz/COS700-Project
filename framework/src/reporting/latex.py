"""Renders a `Table` as booktabs LaTeX."""
from __future__ import annotations

from pathlib import Path

from .labels import signed
from .tables import Cell, Header, Row, Table


def escape(text: str) -> str:
    return str(text).replace("_", r"\_").replace("&", r"\&").replace("%", r"\%")


def _cell(cell: Cell) -> str:
    text = cell.tex if cell.tex is not None else escape(cell.text)
    return rf"\textbf{{{text}}}" if cell.bold else text


def _header(header: Header) -> str:
    text = header.tex if header.tex is not None else escape(header.text)
    return rf"\multicolumn{{{header.span}}}{{c}}{{{text}}}" if header.span > 1 else text


def _line(cells: list[str]) -> str:
    return " & ".join(cells) + r" \\"


def _row(row: Row) -> str:
    return _line([_cell(row.label)] + [_cell(c) for c in row.cells])


def toLatex(table: Table) -> str:
    lines = [
        r"\begin{table}[H]",
        r"\centering",
        r"\small",
    ]
    if table.colsep:
        lines.append(rf"\setlength{{\tabcolsep}}{{{table.colsep}}}")
    lines += [
        rf"\begin{{tabular}}{{{table.align}}}",
        r"\toprule",
    ]
    lines += [_line([_header(h) for h in headerRow]) for headerRow in table.header]
    for section in table.sections:
        lines.append(r"\midrule")
        if section.title:
            lines.append(
                rf"\multicolumn{{{table.width}}}{{l}}{{\textit{{{escape(section.title)}}}}} \\"
            )
            if section.ruleAfterTitle:
                lines.append(r"\midrule")
        lines += [_row(row) for row in section.rows]
    lines += [
        r"\bottomrule",
        r"\end{tabular}",
        rf"\caption{{{table.caption}}}",
        rf"\label{{{table.texLabel}}}",
        r"\end{table}",
    ]
    return "\n".join(lines) + "\n"


def writeTex(content: str | Table, path: Path) -> Path:
    if isinstance(content, Table):
        content = toLatex(content)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path
