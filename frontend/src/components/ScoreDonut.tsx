interface ScoreDonutProps { score: number; }

const getColor = (score: number) => {
  if (score >= 90) return "text-emerald-400";
  if (score >= 75) return "text-emerald-400";
  if (score >= 50) return "text-amber-400";
  if (score >= 25) return "text-orange-400";
  return "text-red-400";
};

const getLabel = (score: number) => {
  if (score >= 90) return "Excellent";
  if (score >= 75) return "Good";
  if (score >= 50) return "Fair";
  if (score >= 25) return "Needs work";
  return "Critical";
};

export default function ScoreDonut({ score }: ScoreDonutProps) {
  const color = getColor(score);
  const label = getLabel(score);
  const circumference = 2 * Math.PI * 24;
  const offset = circumference * (1 - Math.max(0, Math.min(100, score)) / 100);

  return (
    <div className="panel p-6 fade-in">
      <div className="flex items-center justify-between mb-4">
        <div>
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Code quality score</p>
          <p className={`text-3xl font-bold ${color}`}>{Math.max(0, score)}</p>
        </div>
        <span className={`px-2.5 py-1 rounded-md text-xs font-bold border ${color === "text-emerald-400" ? "border-emerald-500/20 bg-emerald-500/5" : color === "text-amber-400" ? "border-amber-500/20 bg-amber-500/5" : color === "text-orange-400" ? "border-orange-500/20 bg-orange-500/5" : "border-red-500/20 bg-red-500/5"}`}>
          {label}
        </span>
      </div>
      <div className="relative w-24 h-24 mx-auto mb-2">
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 50 50">
          <circle
            cx="25"
            cy="25"
            r="24"
            fill="none"
            stroke="white/5"
            strokeWidth="4"
          />
          <circle
            cx="25"
            cy="25"
            r="24"
            fill="none"
            stroke="currentColor"
            strokeWidth="4"
            strokeLinecap="round"
            className={color}
            style={{ strokeDasharray: circumference, strokeDashoffset: offset, transition: "stroke-dashoffset 0.8s ease-out" }}
          />
        </svg>
      </div>
      <p className="text-xs text-slate-500 text-center">Severity-weighted. Lower findings = higher score.</p>
    </div>
  );
}
