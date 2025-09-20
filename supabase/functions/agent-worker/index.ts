import { createClient } from "jsr:@supabase/supabase-js@2";

const CORAL_URL = Deno.env.get("CORAL_URL")!;
const OPENAI_KEY = Deno.env.get("OPENAI_API_KEY")!;

async function processOne(supabase: any) {
  const { data: popped, error: popErr } = await supabase
    .schema("pgmq_public")
    .rpc("pop", { queue_name: "agent_runs" });

  if (popErr || !popped?.message) return null;

  const msg = popped.message as any;
  const { run_id } = msg;

  await supabase.from("runs").update({ status: "running", started_at: new Date().toISOString() }).eq("id", run_id);

  const resp = await fetch(`${CORAL_URL}/orchestrate`, {
    method: "POST",
    headers: { "content-type": "application/json", "authorization": `Bearer ${OPENAI_KEY}` },
    body: JSON.stringify(msg),
  });

  const text = await resp.text();

  await supabase.from("messages").insert({ run_id, role: "assistant", content: text });
  await supabase.from("runs").update({ status: "succeeded", finished_at: new Date().toISOString() }).eq("id", run_id);

  await supabase.rpc("realtime.send", [
    { run_id, state: "succeeded" } as unknown as object,
    "status",
    `run:${run_id}`,
    false
  ] as unknown as Record<string, unknown>);

  await supabase.schema("pgmq_public").rpc("archive", { queue_name: "agent_runs", msg_id: popped.msg_id });

  return run_id;
}

Deno.serve(async (_req) => {
  const supabase = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!);

  for (let i = 0; i < 5; i++) {
    const done = await processOne(supabase);
    if (!done) break;
  }
  return new Response("ok");
});






