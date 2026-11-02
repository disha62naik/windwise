import { useState } from "react";
import { Shell, type View } from "../components/layout/Shell";
import { ErrorState, Loading } from "../components/feedback/States";
import { IntervalTable } from "../components/tables/IntervalTable";
import { Accuracy } from "../features/accuracy/Accuracy";
import { Dashboard } from "../features/dashboard/Dashboard";
import { DataQuality } from "../features/data-quality/DataQuality";
import { Methodology } from "../features/methodology/Methodology";
import { useDayForecast } from "../hooks/useApi";

const MONTH = "2026-01";

function TableView({ date }: { date: string }) {
  const q = useDayForecast(date);
  if (q.isLoading) return <Loading />;
  if (q.error) return <ErrorState message={(q.error as Error).message} onRetry={() => q.refetch()} />;
  return <IntervalTable records={q.data!.records} date={date} />;
}

export default function App() {
  const [view, setView] = useState<View>("dashboard");
  const [date, setDate] = useState("2026-01-15");
  return (
    <Shell view={view} onView={setView} date={date} onDate={setDate}>
      {view === "dashboard" && <Dashboard date={date} />}
      {view === "accuracy" && <Accuracy month={MONTH} onPickDate={(d) => { setDate(d); setView("dashboard"); }} />}
      {view === "table" && <TableView date={date} />}
      {view === "quality" && <DataQuality month={MONTH} />}
      {view === "method" && <Methodology />}
    </Shell>
  );
}
