import type { TeamMarket } from "@/lib/types";
import { signedPct, signedUnits } from "@/lib/format";

export default function TeamRoiTable({ rows }: { rows: TeamMarket[] }) {
  return (
    <div className="card table-card">
      <div className="section-header">
        <div>
          <h2>Team market value</h2>
          <p>Shifted YTD ROI layer for ML, run line and totals.</p>
        </div>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Team</th>
              <th>Value score</th>
              <th>ML ROI</th>
              <th>RL ROI</th>
              <th>O/U ROI</th>
              <th>ML Profit</th>
              <th>RL Profit</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.team}>
                <td><strong>{r.team}</strong></td>
                <td className={r.value_score >= 0 ? "positive" : "negative"}>{signedPct(r.value_score, 1)}</td>
                <td className={r.ml_roi_ytd >= 0 ? "positive" : "negative"}>{signedPct(r.ml_roi_ytd, 1)}</td>
                <td className={r.rl_roi_ytd >= 0 ? "positive" : "negative"}>{signedPct(r.rl_roi_ytd, 1)}</td>
                <td className={r.ou_roi_ytd >= 0 ? "positive" : "negative"}>{signedPct(r.ou_roi_ytd, 1)}</td>
                <td className={r.ml_profit_ytd >= 0 ? "positive" : "negative"}>{signedUnits(r.ml_profit_ytd)}</td>
                <td className={r.rl_profit_ytd >= 0 ? "positive" : "negative"}>{signedUnits(r.rl_profit_ytd)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
