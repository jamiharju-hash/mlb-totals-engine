import type { Projection } from "@/lib/types";
import { pct } from "@/lib/format";

export default function EdgeBars({ rows }: { rows: Projection[] }) {
  const sorted = [...rows].sort((a, b) => b.edge_pct - a.edge_pct).slice(0, 8);

  return (
    <div className="card">
      <div className="section-header">
        <div>
          <h2>Top edges</h2>
          <p>Largest model probability advantage against market probability.</p>
        </div>
      </div>

      <div className="bars">
        {sorted.map((r) => {
          const width = Math.min(Math.abs(r.edge_pct) * 800, 100);
          return (
            <div className="bar-row" key={`${r.game_id}-${r.selection}`}>
              <div className="bar-label">
                <strong>{r.selection}</strong>
                <span>{r.team} {r.home_away === "home" ? "vs" : "@"} {r.opponent}</span>
              </div>
              <div className="bar-track">
                <div
                  className={r.edge_pct >= 0 ? "bar-fill positive-bg" : "bar-fill negative-bg"}
                  style={{ width: `${width}%` }}
                />
              </div>
              <div className={r.edge_pct >= 0 ? "positive bar-value" : "negative bar-value"}>
                {pct(r.edge_pct, 1)}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
