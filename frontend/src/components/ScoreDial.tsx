interface ScoreDialProps { score: number; }

const getColor = (score: number) => {
  if (score >= 90) return { color: "var(--success)", label: "Excellent" };
  if (score >= 75) return { color: "var(--success)", label: "Great" };
  if (score >= 50) return { color: "var(--warn)", label: "Fair" };
  if (score >= 25) return { color: "var(--warn)", label: "Needs work" };
  return { color: "var(--danger)", label: "Critical" };
};

export default function ScoreDial({ score }: ScoreDialProps) {
  const { color, label } = getColor(score);
  const circumference = 2 * Math.PI * 40;
  const offset = circumference * (1 - Math.max(0, Math.min(100, score)) / 100);

  return (
    <div className="score-wrap">
      <div className="score-dial">
        <svg viewBox="0 0 88 88">
          <circle className="track" cx="44" cy="44" r="40" />
          <circle
            className="progress"
            cx="44"
            cy="44"
            r="40"
            style={{
              stroke: color,
              strokeDasharray: circumference,
              strokeDashoffset: offset,
            }}
          />
        </svg>
      </div>
      <div className="score-value">
        <span className="score-number">{Math.max(0, score)}</span>
        <span className="score-label" style={{ color: color }}>
          {label}
        </span>
      </div>
      <p className="score-caption">Severity-weighted score, 0-100</p>
    </div>
  );
}
