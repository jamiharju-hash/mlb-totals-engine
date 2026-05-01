import type { Projection } from "@/lib/types";
import { pct, num } from "@/lib/format";
import SignalBadge from "./SignalBadge";

type Props = {
  rows: Projection[];
};

export default function ProjectionTable({ rows }: Props) {
  return (
    <div className="card table-card">
      <div className="section-header">
        <div>
          <h2>Daily projections</h2>
          <p>Final probability vs market probability, with edge and recommended stake.</p>
        </div>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Signal</th>
              <th>Team</th>
              <th>Market</th>
              <th>Selection</th>
              <th>Model</th>
              <th>Market</th>
              <th>Edge</th>
              <th>Stake</th>
              <th>Override</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={`${r.game_id}-${r.team}-${r.market}-${r.selection}`}>
                <td><SignalBadge signal={r.bet_signal} /></td>
                <td>
                  <div className="team-cell">
                    <strong>{r.team}</strong>
                    <span>{r.home_away === "home" ? "vs" : "@"} {r.opponent}</span>
                  </div>
                </td>
                <td>{r.market}</td>
                <td>{r.selection}</td>
                <td>{pct(r.final_probability, 1)}</td>
                <td>{pct(r.market_probability, 1)}</td>
                <td className={r.edge_pct >= 0 ? "positive" : "negative"}>{pct(r.edge_pct, 1)}</td>
                <td>{num(r.stake_units, 2)}u</td>
                <td>{r.manual_override_flag ? "Yes" : "No"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
