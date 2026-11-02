import { BarChart3, BookOpen, LayoutDashboard, ShieldCheck, Table2, Wind } from "lucide-react";
import type { ReactNode } from "react";

export type View = "dashboard" | "accuracy" | "table" | "quality" | "method";
const NAV = [
  { id: "dashboard", label: "Dashboard", Icon: LayoutDashboard },
  { id: "accuracy", label: "Historical accuracy", Icon: BarChart3 },
  { id: "table", label: "Settlement periods", Icon: Table2 },
  { id: "quality", label: "Data quality", Icon: ShieldCheck },
  { id: "method", label: "Methodology", Icon: BookOpen },
] as const;

interface Props { view: View; onView: (v: View) => void; date: string; onDate: (d: string) => void; children: ReactNode }

export function Shell({ view, onView, date, onDate, children }: Props) {
  return (
    <div className="flex min-h-screen flex-col md:flex-row">
      <nav aria-label="Main" className="bg-navy-900 p-3 text-slate-200 md:w-56 md:shrink-0">
        <p className="mb-3 flex items-center gap-2 px-2 text-lg font-semibold text-white"><Wind className="h-5 w-5 text-green-400" aria-hidden /> WindWise</p>
        <ul className="flex gap-1 overflow-x-auto md:block md:space-y-1">
          {NAV.map(({ id, label, Icon }) => (
            <li key={id}>
              <button onClick={() => onView(id)} aria-current={view === id ? "page" : undefined}
                className={`flex w-full items-center gap-2 whitespace-nowrap rounded px-3 py-2 text-left text-sm ${view === id ? "bg-navy-700 text-white" : "hover:bg-navy-800"}`}>
                <Icon className="h-4 w-4" aria-hidden /> {label}
              </button>
            </li>
          ))}
        </ul>
      </nav>
      <main className="min-w-0 flex-1 p-4 md:p-6">
        <header className="mb-4 flex flex-wrap items-end justify-between gap-3">
          <h1 className="text-xl font-semibold">Wind forecast intelligence — January 2026</h1>
          <label className="text-sm">
            <span className="block text-slate-600">Delivery date (Europe/London)</span>
            <input type="date" value={date} min="2026-01-01" max="2026-01-31" onChange={(e) => e.target.value && onDate(e.target.value)} className="rounded border border-slate-300 bg-white px-2 py-1" />
          </label>
        </header>
        {children}
      </main>
    </div>
  );
}
