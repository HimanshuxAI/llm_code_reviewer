import { Code2 } from "lucide-react";

interface EmptyStateProps { title: string; subtitle: string; action?: React.ReactNode; }

export default function EmptyState({ title, subtitle, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <div className="w-16 h-16 rounded-2xl bg-slate-800 border border-white/10 flex items-center justify-center mb-6 text-slate-500">
        <Code2 className="h-8 w-8" />
      </div>
      <h2 className="text-lg font-semibold text-white">{title}</h2>
      <p className="mt-2 text-sm text-slate-400 max-w-xs">{subtitle}</p>
      {action && <div className="mt-8">{action}</div>}
    </div>
  );
}
