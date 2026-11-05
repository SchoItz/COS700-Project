import { useMemo, useState } from "react";
import type { Employee } from "../api";
import { Badge } from "./ui";

export default function EmployeeTable({ employees }: { employees: Employee[] }) {
  const [filter, setFilter] = useState<"all" | "drifted" | "benign">("all");
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    return employees.filter((e) => {
      if (filter === "drifted" && !e.drifted) return false;
      if (filter === "benign" && e.drifted) return false;
      if (search && !e.employee_id.toLowerCase().includes(search.toLowerCase())) return false;
      return true;
    });
  }, [employees, filter, search]);

  return (
    <div className="panel">
      <div className="panel-header">
        <h3>Employees ({filtered.length})</h3>
        <div className="panel-controls">
          <input
            placeholder="Search employee id…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <select value={filter} onChange={(e) => setFilter(e.target.value as typeof filter)}>
            <option value="all">All</option>
            <option value="drifted">Drifted only</option>
            <option value="benign">Benign only</option>
          </select>
        </div>
      </div>
      <div className="table-scroll tall">
        <table>
          <thead>
            <tr>
              <th>Employee</th>
              <th>Department</th>
              <th>Role</th>
              <th>Total events</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {filtered.slice(0, 200).map((e) => (
              <tr key={e.employee_id}>
                <td>{e.employee_id}</td>
                <td>{e.department}</td>
                <td>{e.role}</td>
                <td>{e.total_events.toLocaleString()}</td>
                <td>
                  <Badge tone={e.drifted ? "red" : "green"}>{e.drifted ? "Drifted" : "Benign"}</Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {filtered.length > 200 && (
        <div className="table-note">Showing first 200 of {filtered.length} results.</div>
      )}
    </div>
  );
}
