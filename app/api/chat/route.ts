import { NextResponse } from "next/server";

type ReqBody = { message?: string };

export async function POST(request: Request) {
  try {
    const body: ReqBody = await request.json().catch(() => ({}));
    const userMsg = body?.message ?? "Hello traveler";

    // Simulate processing delay
    await new Promise((r) => setTimeout(r, 700));

    const reply = `MockBot: I received "${String(userMsg)}".\n\nTravel tips:\n• Pack light\n• Check local transit\n• Try a local specialty\n\nSafe travels!`;

    return NextResponse.json({ reply });
  } catch (err) {
    return NextResponse.json({ error: "internal server error" }, { status: 500 });
  }
}
