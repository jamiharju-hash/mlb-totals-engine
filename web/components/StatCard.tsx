type Props = {
  label: string;
  value: string | number;
  sublabel?: string;
};

export default function StatCard({ label, value, sublabel }: Props) {
  return (
    <div className="card stat-card">
      <div className="muted small">{label}</div>
      <div className="stat-value">{value}</div>
      {sublabel ? <div className="muted small">{sublabel}</div> : null}
    </div>
  );
}
