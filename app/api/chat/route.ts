import type { NextRequest } from "next/server";

function inferMaxTokens(message: string): number {
  const m = message.match(/(\d+)[- ]day/i);
  if (m) {
    const days = parseInt(m[1], 10);
    if (days >= 7) return 3000;
    if (days >= 5) return 2500;
    if (days >= 3) return 2000;
  }
  return 1500;
}

export async function POST(request: NextRequest) {
  const body = await request.json();

  const res = await fetch("https://vegan-audacious-crumpled.ngrok-free.dev/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: body.session_id,
      message: body.message,
      model_variant: "fine_tuned",
      max_new_tokens: inferMaxTokens(body.message ?? ""),
      include_raw_model_output: false,
    }),
  });

  if (!res.ok) {
    return Response.json(
      { error: "Backend error", status: res.status },
      { status: 502 }
    );
  }

  const data = await res.json();

  return Response.json({
    assistant_message: data.assistant_message,
    dashboard_payload: data.dashboard_payload ?? null,
    fallback_used: data.fallback_used ?? false,
    parse_success: data.parse_success ?? true,
  });
}
