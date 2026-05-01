export default function SignalBadge({ signal }: { signal: string }) {
  return <span className={`badge badge-${signal.toLowerCase()}`}>{signal.replace("_", " ")}</span>;
}
