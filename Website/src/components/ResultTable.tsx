import type { Table } from "../api";

/** Renders a results table exactly as the backend built it -- the same cells,
 * rounding, labels and bold best value as the corresponding table in the
 * paper. Nothing is reformatted here. */
export default function ResultTable({ table }: { table: Table }) {
  const alignOf = (i: number) =>
    ({ l: "left", r: "right", c: "center" })[table.align[i]] as "left" | "right" | "center";

  return (
    <div className="result-table">
      <div className="table-scroll">
        <table>
          <thead>
            {table.header.map((row, r) => (
              <tr key={r}>
                {row.map((h, i) => (
                  <th
                    key={i}
                    colSpan={h.span}
                    style={{ textAlign: h.span > 1 ? "center" : alignOf(i) }}
                  >
                    {h.text}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          {table.sections.map((section, s) => (
            <tbody key={s} className="table-section">
              {section.title && (
                <tr className="section-title">
                  <td colSpan={table.align.length}>{section.title}</td>
                </tr>
              )}
              {section.rows.map((row, r) => (
                <tr key={r}>
                  <td>{row.label.text}</td>
                  {row.cells.map((cell, c) => (
                    <td
                      key={c}
                      className={cell.bold ? "best" : undefined}
                      style={{ textAlign: alignOf(c + 1) }}
                    >
                      {cell.text}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          ))}
        </table>
      </div>
      <p className="table-note">{table.caption}</p>
    </div>
  );
}
