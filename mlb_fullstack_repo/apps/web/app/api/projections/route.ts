import { NextResponse } from "next/server";
import { createAnonSupabaseClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

export async function GET() {
  const supabase = createAnonSupabaseClient();
  const { data, error } = await supabase
    .from("projections")
    .select("*")
    .order("game_date", { ascending: false })
    .order("edge_pct", { ascending: false })
    .limit(200);

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ data });
}
