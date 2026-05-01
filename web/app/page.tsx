"use client";

import { useEffect, useMemo, useState } from "react";
import type { DashboardPayload, Projection } from "@/lib/types";
import { pct } from "@/lib/format";
import StatCard from "@/components/StatCard";
import ProjectionTable from "@/components/ProjectionTable";
import TeamRoiTable from "@/components/TeamRoiTable";
import EdgeBars from "@/components/EdgeBars";
import ModelMetrics from "@/components/ModelMetrics";

const marketOptions = ["all", "moneyline", "runline", "total"];
const signalOptions = ["all", "BET_STRONG", "BET_SMALL", "NO_BET", "FADE"];

export default function Home() {
  const [data, setData] = useState<DashboardPayload | null>(null);
  const [market, setMarket] = useState("all");
  const [signal, setSignal] = useState("all");

  useEffect(() => {
    fetch("/data/dashboard.json", { cache: "no-store" })
      .then((res) => {
        if (!res.ok) throw new Error("Failed to load dashboard.json");
        return res.json();
      })
      .then(setData)
      .catch((err) => console.error(err));
  }, []);

  const filtered = useMemo(() => {
    if (!data) return [] as Projection[];

    return data.projections
      .filter((r) => market === "all" || r.market === market)
      .filter((r) => signal === "all" || r.bet_signal === signal)
      .sort((a, b) => b.edge_pct - a.edge_pct);
  }, [data, market, signal]);

  if (!data) {
    return (
      <main className="container">
        <div className="card">
          <h1>Loading MLB Projection Dashboard…</h1>
          <p className="muted">Run the Python pipeline if dashboard.json does not exist.</p>
        </div>
      </main>
    );
  }

  const best = [...data.projections].sort((a, b) => b.edge_pct - a.edge_pct)[0];

  return (
    <main className="container">
      <header className="hero">
        <div>
          <div className="eyebrow">MLB Projection Engine</div>
          <h1>Daily betting projections</h1>
          <p>
            Semi-automated model output combining pitcher form, handedness,
            weather, market pricing, team ROI and manual overrides.
          </p>
        </div>
        <div className="timestamp">
          Generated<br />
          <strong>{new Date(data.generated_at).toLocaleString()}</strong>
        </div>
      </header>

      <section className="stats-grid">
        <StatCard label="Projections" value={data.summary.projection_count} />
        <StatCard label="Bet signals" value={data.summary.bet_count} sublabel={`${data.summary.strong_bet_count} strong`} />
        <StatCard label="Average edge" value={pct(data.summary.average_edge_pct, 1)} />
        <StatCard label="Max edge" value={pct(data.summary.max_edge_pct, 1)} sublabel={best?.selection} />
        <StatCard label="Teams tracked" value={data.summary.teams_tracked} />
      </section>

      <section className="controls card">
        <div>
          <label>Market</label>
          <select value={market} onChange={(e) => setMarket(e.target.value)}>
            {marketOptions.map((m) => <option key={m} value={m}>{m}</option>)}
          </select>
        </div>

        <div>
          <label>Signal</label>
          <select value={signal} onChange={(e) => setSignal(e.target.value)}>
            {signalOptions.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
      </section>

      <section className="grid-two">
        <EdgeBars rows={filtered} />
        <ModelMetrics metrics={data.model_metrics} />
      </section>

      <ProjectionTable rows={filtered} />

      <TeamRoiTable rows={data.team_market} />
    </main>
  );
}
