import type { DashboardPayload } from "@/lib/types";
import { pct, num } from "@/lib/format";

export default function ModelMetrics({ metrics }: { metrics: DashboardPayload["model_metrics"] }) {
  return (
    <div className="card">
      <div className="section-header">
        <div>
          <h2>Model metrics</h2>
          <p>{metrics.model_version} · {metrics.as_of}</p>
        </div>
      </div>

      <div className="metric-grid">
        <div>
          <span className="muted small">Start score MAE</span>
          <strong>{num(metrics.test_mae_start_score, 2)}</strong>
        </div>
        <div>
          <span className="muted small">Runline AUC</span>
          <strong>{num(metrics.test_auc_runline, 3)}</strong>
        </div>
        <div>
          <span className="muted small">Moneyline AUC</span>
          <strong>{num(metrics.test_auc_moneyline, 3)}</strong>
        </div>
        <div>
          <span className="muted small">Simulated ROI</span>
          <strong>{pct(metrics.simulated_roi_last_250, 1)}</strong>
        </div>
        <div>
          <span className="muted small">Avg CLV</span>
          <strong>{pct(metrics.avg_clv_last_250, 1)}</strong>
        </div>
      </div>

      {metrics.notes ? <p className="muted">{metrics.notes}</p> : null}
    </div>
  );
}
