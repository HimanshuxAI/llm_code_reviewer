import { Code2 } from "lucide-react";

interface EmptyStateProps { title: string; subtitle: string; action?: React.ReactNode; }

export default function EmptyState({ title, subtitle, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <div className="w-20 h-20 rounded-2xl bg-blue-50 border border-blue-100 flex items-center justify-center mb-7 text-blue-500">
        <Code2 className="h-9 w-9" />
      </div>
      <h2 className="text-lg font-bold text-slate-800">{title}</h2>
      <p className="mt-3 text-sm text-slate-500 max-w-xs">{subtitle}</p>
      {action && <div className="mt-9">{action}</div>}
    </div>
  );
}
