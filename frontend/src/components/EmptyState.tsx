

interface EmptyStateProps { title: string; subtitle: string; action?: React.ReactNode; }

export default function EmptyState({ title, subtitle, action }: EmptyStateProps) {
  return (
    <div className="empty">
      <div className="empty-mark">!</div>
      <h2 className="empty-title">{title}</h2>
      <p className="empty-sub">{subtitle}</p>
      {action && <div>{action}</div>}
    </div>
  );
}
