import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  fetchActivityAverages,
  fetchCorpusSummary,
  fetchEmployees,
  fetchWeekdayCounts,
  type ActivityAverageRow,
  type CorpusSummary,
  type Employee,
  type WeekdayCount,
} from "../api";
import ActivityAveragesChart from "../components/ActivityAveragesChart";
import DriftTrendChart from "../components/DriftTrendChart";
import EmployeeTable from "../components/EmployeeTable";
import StatCards from "../components/StatCards";
import { ApiStatus, PageHeader } from "../components/ui";
import WeekdayCountsChart from "../components/WeekdayCountsChart";

export default function CorpusPage() {
  const [summary, setSummary] = useState<CorpusSummary | null>(null);
  const [weekdayCounts, setWeekdayCounts] = useState<WeekdayCount[]>([]);
  const [activityAverages, setActivityAverages] = useState<ActivityAverageRow[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([fetchCorpusSummary(), fetchWeekdayCounts(), fetchActivityAverages(), fetchEmployees()])
      .then(([s, wc, aa, emp]) => {
        setSummary(s);
        setWeekdayCounts(wc);
        setActivityAverages(aa);
        setEmployees(emp);
      })
      .catch((e) => setError(String(e)));
  }, []);

  return (
    <>
      <PageHeader
        crumbs={
          <>
            <Link to="/data">Data</Link> / Weekday corpus
          </>
        }
        title="Weekday log corpus"
        lead={
          <>
            The full raw weekday corpus behind the paper&apos;s single-day logs
            {summary ? `: ${summary.n_weeks.toLocaleString()} weeks per employee` : ""}. The paper
            evaluates on a 20-week window per employee taken from it, so these counts are larger
            than the paper&apos;s.
          </>
        }
      />
      <ApiStatus what="the corpus" loading={!summary} error={error} />
      {summary && (
        <>
          <StatCards summary={summary} />
          <div className="grid-2">
            <WeekdayCountsChart data={weekdayCounts} />
            <ActivityAveragesChart data={activityAverages} />
          </div>
          <DriftTrendChart />
          <EmployeeTable employees={employees} />
        </>
      )}
    </>
  );
}
