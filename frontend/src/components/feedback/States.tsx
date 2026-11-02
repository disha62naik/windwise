import { AlertTriangle, Inbox, Loader2 } from "lucide-react";
import type { ReactNode } from "react";

export function Loading({ label = "Loading data from the WindWise API…" }: { label?: string }) {
  return (
    <div role="status" className="flex items-center gap-2 p-6 text-slate-600">
      <Loader2 className="h-5 w-5 animate-spin" aria-hidden /> {label}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div role="alert" className="m-4 rounded-lg border border-red-300 bg-red-50 p-4 text-red-900">
      <p className="flex items-center gap-2 font-semibold"><AlertTriangle className="h-5 w-5" aria-hidden /> Data could not be loaded</p>
      <p className="mt-1 text-sm">{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="mt-3 rounded bg-red-700 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-800">
          Retry
        </button>
      )}
    </div>
  );
}

export function EmptyState({ children }: { children: ReactNode }) {
  return (
    <div className="m-4 rounded-lg border border-dashed border-slate-300 bg-white p-6 text-slate-600">
      <p className="flex items-center gap-2 font-semibold"><Inbox className="h-5 w-5" aria-hidden /> No matched intervals</p>
      <div className="mt-1 text-sm">{children}</div>
    </div>
  );
}

export function WarningBanner({ title, items }: { title: string; items: string[] }) {
  if (items.length === 0) return null;
  return (
    <div role="note" className="rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">
      <p className="font-semibold">{title}</p>
      <ul className="ml-5 list-disc">{items.map((w) => <li key={w}>{w}</li>)}</ul>
    </div>
  );
}
