// Deno runtime
import { createClient } from "jsr:@supabase/supabase-js@2";

export const handler = async (req: Request) => {
  if (req.method !== "POST") return new Response("Method Not Allowed", { status: 405 });

  const body = await req.json().catch(() => ({}));
  const { agent_id, candidate_id, company_id, params = {} } = body;

  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
  );

  const { data: runRow, error: runErr } = await supabase
    .from("runs")
    .insert({ agent_id, candidate_id, company_id, status: "queued", params })
    .select()
    .single();

  if (runErr) return new Response(runErr.message, { status: 500 });

  const payload = { run_id: runRow.id, agent_id, candidate_id, company_id, params };
  const { error: qErr } = await supabase
    .schema("pgmq")
    .rpc("send", { queue_name: "agent_runs", msg: payload });

  if (qErr) return new Response(qErr.message, { status: 500 });

  await supabase.rpc("realtime.send", [
    { hello: "queued", run_id: runRow.id } as unknown as object,
    "status",
    `run:${runRow.id}`,
    false
  ] as unknown as Record<string, unknown>);

  return new Response(JSON.stringify({ run_id: runRow.id }), { status: 202 });
};

Deno.serve(handler);






