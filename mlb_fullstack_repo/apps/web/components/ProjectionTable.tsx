import type { Projection } from "@/lib/types";
import { num, pct } from "@/lib/format";
import SignalBadge from "./SignalBadge";

export default function ProjectionTable({ rows }: { rows: Projection[] }) {
  return (
    <div className="card table-card">
      <div className="section-header">
        <div>
          <h2>Daily projections</h2>
          <p>Model probability vs market probability with calculated edge and stake.</p>
        </div>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Signal</th><th>Team</th><th>Market</th><th>Selection</th>
              <th>Model</th><th>Market</th><th>Edge</th><th>Stake</th><th>Override</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={`${r.game_id}-${r.team}-${r.market}-${r.selection}`}>
                <td><SignalBadge signal={r.bet_signal} /></td>
                <td><div className="team-cell"><strong>{r.team}</strong><span>{r.home_away === "home" ? "vs" : "@"} {r.opponent}</span></div></td>
                <td>{r.market}</td>
                <td>{r.selection}</td>
                <td>{pct(r.final_probability)}</td>
                <td>{pct(r.market_probability)}</td>
                <td className={(r.edge_pct ?? 0) >= 0 ? "positive" : "negative"}>{pct(r.edge_pct)}</td>
                <td>{num(r.stake_units)}u</td>
                <td>{r.manual_override_flag ? "Yes" : "No"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
