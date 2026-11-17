interface ScoreDialProps { score: number; }

const getColor = (score: number) => {
  if (score >= 90) return { color: "var(--good)", label: "Excellent" };
  if (score >= 75) return { color: "var(--good)", label: "Great" };
  if (score >= 50) return { color: "var(--mid)", label: "Fair" };
  if (score >= 25) return { color: "var(--mid)", label: "Needs work" };
  return { color: "var(--bad)", label: "Critical" };
};

/* A circled grade: the score drawn inside a red-pen ring with a hand-drawn
   wobble, plus a short overlapping second stroke like a real pen circle. */
export default function ScoreDial({ score }: ScoreDialProps) {
  const { color, label } = getColor(score);

  return (
    <div className="score-wrap">
      <div className="score-dial">
        <svg viewBox="0 0 120 120" style={{ color }} aria-hidden="true">
          <path
            className="pen"
            d="M 63 17 C 88 16 107 35 106 59 C 105 85 84 104 58 104 C 33 104 14 86 15 60 C 16 34 38 18 63 17"
          />
          <path
            className="pen overlap"
            d="M 61 19.5 C 70 18 80 20 87 25"
          />
        </svg>
        <div className="score-value">
          <span className="score-number">{Math.max(0, score)}</span>
          <span className="score-label" style={{ color: color }}>
            {label}
          </span>
        </div>
      </div>
      <p className="score-caption">Severity-weighted score, 0-100</p>
    </div>
  );
}
