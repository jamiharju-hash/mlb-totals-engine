import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { createServiceSupabaseClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

const projectionSchema = z.object({
  game_id: z.string(),
  game_date: z.string(),
  team: z.string(),
  opponent: z.string(),
  home_away: z.enum(["home", "away"]),
  market: z.enum(["moneyline", "runline", "total"]),
  selection: z.string(),
  decimal_odds: z.number().nullable().optional(),
  american_odds: z.number().nullable().optional(),
  market_probability: z.number().nullable().optional(),
  base_probability: z.number().nullable().optional(),
  final_probability: z.number().nullable().optional(),
  edge_pct: z.number().nullable().optional(),
  stake_units: z.number().nullable().optional(),
  stake_pct_bankroll: z.number().nullable().optional(),
  bet_signal: z.enum(["BET_STRONG", "BET_SMALL", "NO_BET", "FADE"]),
  model_confidence: z.number().nullable().optional(),
  pitcher_adjustment: z.number().nullable().optional(),
  lineup_adjustment: z.number().nullable().optional(),
  handedness_adjustment: z.number().nullable().optional(),
  weather_adjustment: z.number().nullable().optional(),
  bullpen_adjustment: z.number().nullable().optional(),
  manual_override: z.number().nullable().optional(),
  manual_override_flag: z.boolean().optional()
});

const teamMarketSchema = z.object({
  as_of_date: z.string(),
  team: z.string(),
  ml_roi_ytd: z.number().nullable().optional(),
  rl_roi_ytd: z.number().nullable().optional(),
  ou_roi_ytd: z.number().nullable().optional(),
  ml_profit_ytd: z.number().nullable().optional(),
  rl_profit_ytd: z.number().nullable().optional(),
  ou_profit_ytd: z.number().nullable().optional(),
  value_score: z.number().nullable().optional()
});

const metricsSchema = z.object({
  as_of: z.string(),
  model_version: z.string(),
  test_mae_start_score: z.number().nullable().optional(),
  test_auc_runline: z.number().nullable().optional(),
  test_auc_moneyline: z.number().nullable().optional(),
  simulated_roi_last_250: z.number().nullable().optional(),
  avg_clv_last_250: z.number().nullable().optional(),
  notes: z.string().nullable().optional()
});

const payloadSchema = z.object({
  projections: z.array(projectionSchema).default([]),
  team_market: z.array(teamMarketSchema).default([]),
  model_metrics: metricsSchema.optional()
});

export async function POST(request: NextRequest) {
  const expected = process.env.PIPELINE_INGEST_SECRET;
  const provided = request.headers.get("x-pipeline-secret");

  if (!expected || provided !== expected) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const parsed = payloadSchema.safeParse(await request.json());
  if (!parsed.success) {
    return NextResponse.json({ error: "Invalid payload", details: parsed.error.flatten() }, { status: 400 });
  }

  const supabase = createServiceSupabaseClient();
  const { projections, team_market, model_metrics } = parsed.data;

  if (projections.length > 0) {
    const { error } = await supabase.from("projections").upsert(
      projections,
      { onConflict: "game_id,team,market,selection" }
    );
    if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  }

  if (team_market.length > 0) {
    const { error } = await supabase.from("team_market_features").upsert(
      team_market,
      { onConflict: "as_of_date,team" }
    );
    if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  }

  if (model_metrics) {
    const { error } = await supabase.from("model_metrics").insert(model_metrics);
    if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json({ ok: true, projections: projections.length, team_market: team_market.length });
}
