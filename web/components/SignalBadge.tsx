import type { BetSignal } from "@/lib/types";

export default function SignalBadge({ signal }: { signal: BetSignal | string }) {
  return <span className={`badge badge-${signal.toLowerCase()}`}>{signal.replace("_", " ")}</span>;
}
