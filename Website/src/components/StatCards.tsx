import type { CorpusSummary } from "../api";
import { Stat } from "./ui";

export default function StatCards({ summary }: { summary: CorpusSummary }) {
  const cards = [
    { label: "Records (full corpus)", value: summary.total_records.toLocaleString() },
    { label: "Employees", value: summary.n_employees.toLocaleString() },
    { label: "Drifted employees", value: summary.n_drifted_employees.toLocaleString() },
    { label: "Weeks observed", value: summary.n_weeks.toLocaleString() },
    { label: "Weekday files", value: summary.n_files.toLocaleString() },
    {
      label: "Date range",
      value: `${summary.date_range.start} → ${summary.date_range.end}`,
      wide: true,
    },
  ];

  return (
    <div className="stat-grid">
      {cards.map((c) => (
        <Stat key={c.label} value={c.value} label={c.label} wide={c.wide} />
      ))}
    </div>
  );
}
