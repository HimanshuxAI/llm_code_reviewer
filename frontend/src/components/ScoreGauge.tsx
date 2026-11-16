interface ScoreGaugeProps {
  score: number;
}

export default function ScoreGauge({ score }: ScoreGaugeProps) {
  let label: string;
  let color: string;
  if (score >= 90) {
    label = "Excellent";
    color = "text-green-600 bg-green-50 border-green-100";
  } else if (score >= 75) {
    label = "Good";
    color = "text-green-600 bg-green-50 border-green-100";
  } else if (score >= 50) {
    label = "Fair";
    color = "text-amber-700 bg-amber-50 border-amber-100";
  } else if (score >= 25) {
    label = "Needs work";
    color = "text-amber-700 bg-amber-50 border-amber-100";
  } else {
    label = "Critical";
    color = "text-red-600 bg-red-50 border-red-100";
  }

  return (
    <div className="panel p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm font-medium text-gray-700">Code quality score</span>
        <span className={`text-2xl font-bold ${color.split(" ")[0]}`}>{score}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-3">
        <div
          className={`h-3 rounded-full transition-all duration-700 ease-out ${color.includes("green")
            ? "bg-green-600"
            : color.includes("amber")
            ? "bg-amber-500"
            : "bg-red-500"}`}
          style={{ width: `${Math.max(score, 0)}%` }}
        />
      </div>
      <p className={`mt-2 text-sm font-medium ${color}`}>{label}</p>
    </div>
  );
}
