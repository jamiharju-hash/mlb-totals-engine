import { NextResponse } from "next/server";
import { createAnonSupabaseClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

export async function GET() {
  const supabase = createAnonSupabaseClient();
  const { data, error } = await supabase
    .from("model_metrics")
    .select("*")
    .order("as_of", { ascending: false })
    .limit(1)
    .maybeSingle();

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ data });
}
