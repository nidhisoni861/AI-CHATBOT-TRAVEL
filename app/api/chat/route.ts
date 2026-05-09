import type { NextRequest } from "next/server";

export async function POST(request: NextRequest) {
  const body = await request.json();

  const res = await fetch("http://127.0.0.1:9000/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: body.session_id,
      message: body.message,
      model_variant: "fine_tuned",
      max_new_tokens: 600,
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
  });
}
