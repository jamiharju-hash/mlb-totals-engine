import { NextResponse } from "next/server";
import { createAnonSupabaseClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

export async function GET() {
  const supabase = createAnonSupabaseClient();
  const { data, error } = await supabase
    .from("team_market_features")
    .select("*")
    .order("as_of_date", { ascending: false })
    .order("value_score", { ascending: false })
    .limit(200);

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ data });
}
