import ProjectionTable from "@/components/ProjectionTable";
import TeamRoiTable from "@/components/TeamRoiTable";
import StatCard from "@/components/StatCard";
import { pct } from "@/lib/format";
import type { ModelMetrics, Projection, TeamMarket } from "@/lib/types";

async function getJson<T>(path: string, fallback: T): Promise<T> {
  try {
    const baseUrl =
      process.env.NEXT_PUBLIC_SITE_URL ||
      (process.env.VERCEL_URL ? `https://${process.env.VERCEL_URL}` : "http://localhost:3000");

    const res = await fetch(`${baseUrl}${path}`, { cache: "no-store" });
    if (!res.ok) return fallback;
    const json = await res.json();
    return json.data ?? fallback;
  } catch {
    return fallback;
  }
}

export default async function Home() {
  const projections = await getJson<Projection[]>("/api/projections", []);
  const teamMarket = await getJson<TeamMarket[]>("/api/team-market", []);
  const metrics = await getJson<ModelMetrics | null>("/api/model-metrics", null);

  const betCount = projections.filter((p) => ["BET_SMALL", "BET_STRONG"].includes(p.bet_signal)).length;
  const strongCount = projections.filter((p) => p.bet_signal === "BET_STRONG").length;
  const avgEdge = projections.length ? projections.reduce((s, p) => s + Number(p.edge_pct ?? 0), 0) / projections.length : 0;
  const maxEdge = projections.length ? Math.max(...projections.map((p) => Number(p.edge_pct ?? 0))) : 0;

  const signalCounts = projections.reduce<Record<string, number>>((acc, p) => {
    acc[p.bet_signal] = (acc[p.bet_signal] ?? 0) + 1;
    return acc;
  }, {});

  const marketCounts = projections.reduce<Record<string, number>>((acc, p) => {
    acc[p.market] = (acc[p.market] ?? 0) + 1;
    return acc;
  }, {});

  const topTeams = [...teamMarket]
    .sort((a, b) => Number(b.value_score ?? -999) - Number(a.value_score ?? -999))
    .slice(0, 5);

  const maxSignalCount = Math.max(1, ...Object.values(signalCounts));
  const maxMarketCount = Math.max(1, ...Object.values(marketCounts));

  return (
    <main className="container">
      <header className="hero">
        <div>
          <div className="eyebrow">MLB Projection Engine</div>
          <h1>Analytics Dashboard</h1>
          <p>Executive view of daily model opportunities, signal mix, and team-level value concentration.</p>
        </div>
        <div className="timestamp">Model<br /><strong>{metrics?.model_version ?? "not available"}</strong></div>
      </header>

      <section className="stats-grid">
        <StatCard label="Projections" value={projections.length} />
        <StatCard label="Bet signals" value={betCount} sublabel={`${strongCount} strong`} />
        <StatCard label="Average edge" value={pct(avgEdge)} />
        <StatCard label="Max edge" value={pct(maxEdge)} />
        <StatCard label="Teams tracked" value={teamMarket.length} />
      </section>

      <section className="card">
        <div className="section-header">
          <div>
            <h2>Signal distribution</h2>
            <p>Share of projection recommendations by confidence band.</p>
          </div>
        </div>
        <div className="bar-list">
          {Object.entries(signalCounts).map(([signal, count]) => (
            <div key={signal} className="bar-row">
              <div className="bar-label">{signal.replace("_", " ")}</div>
              <div className="bar-track"><div className="bar-fill" style={{ width: `${(count / maxSignalCount) * 100}%` }} /></div>
              <strong>{count}</strong>
            </div>
          ))}
        </div>
      </section>

      <section className="card">
        <div className="section-header">
          <div>
            <h2>Market mix</h2>
            <p>Current distribution across moneyline, runline, and totals markets.</p>
          </div>
        </div>
        <div className="bar-list">
          {Object.entries(marketCounts).map(([market, count]) => (
            <div key={market} className="bar-row">
              <div className="bar-label">{market}</div>
              <div className="bar-track"><div className="bar-fill secondary" style={{ width: `${(count / maxMarketCount) * 100}%` }} /></div>
              <strong>{count}</strong>
            </div>
          ))}
        </div>
      </section>

      <section className="card">
        <div className="section-header">
          <div>
            <h2>Top team opportunities</h2>
            <p>Highest value_score teams from the latest team-market snapshot.</p>
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
                <th>OU ROI</th>
              </tr>
            </thead>
            <tbody>
              {topTeams.map((row) => (
                <tr key={row.team}>
                  <td>{row.team}</td>
                  <td>{row.value_score ?? "—"}</td>
                  <td>{pct(row.ml_roi_ytd)}</td>
                  <td>{pct(row.rl_roi_ytd)}</td>
                  <td>{pct(row.ou_roi_ytd)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <ProjectionTable rows={projections} />
      <TeamRoiTable rows={teamMarket} />

      <div className="card">
        <h2>Model metrics</h2>
        {metrics ? (
          <div className="metric-grid">
            <div><span className="muted small">MAE</span><strong>{metrics.test_mae_start_score ?? "—"}</strong></div>
            <div><span className="muted small">Runline AUC</span><strong>{metrics.test_auc_runline ?? "—"}</strong></div>
            <div><span className="muted small">Moneyline AUC</span><strong>{metrics.test_auc_moneyline ?? "—"}</strong></div>
            <div><span className="muted small">Sim ROI</span><strong>{pct(metrics.simulated_roi_last_250)}</strong></div>
            <div><span className="muted small">Avg CLV</span><strong>{pct(metrics.avg_clv_last_250)}</strong></div>
          </div>
        ) : <p className="muted">No model metrics found. Run the pipeline to insert metrics.</p>}
      </div>
    </main>
  );
}
