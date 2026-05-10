import { NextRequest } from "next/server";

// Google Translate unofficial API — free, no key needed
// sl=auto detects source language automatically
// Returns: [[[translated, original, ...]...], null, "detected-lang-code", ...]
async function googleTranslate(
  text: string,
  targetLang: string
): Promise<{ translated: string; detectedLang: string }> {
  const url =
    `https://translate.googleapis.com/translate_a/single` +
    `?client=gtx&sl=auto&tl=${encodeURIComponent(targetLang)}` +
    `&dt=t&q=${encodeURIComponent(text)}`;

  const res = await fetch(url);
  if (!res.ok) throw new Error(`Google Translate HTTP ${res.status}`);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const data = await res.json() as any[];

  // Collect all translated segments
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const translated = (data[0] as any[])
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    .map((seg: any[]) => seg[0] as string)
    .filter(Boolean)
    .join("");

  // data[2] is the detected source language ISO code e.g. "de", "hi", "en"
  const detectedLang = (data[2] as string | undefined) ?? "en";

  return { translated, detectedLang };
}

export async function POST(request: NextRequest) {
  let text = "";
  let targetLang = "en";

  try {
    const body = await request.json() as { text?: string; targetLang?: string };
    text = body.text ?? "";
    targetLang = body.targetLang ?? "en";

    if (!text.trim()) {
      return Response.json({ translated: text, detectedLang: targetLang });
    }

    const result = await googleTranslate(text, targetLang);
    return Response.json(result);
  } catch (err) {
    console.error("[translate] error:", String(err));
    // Graceful fallback — return original text so the app does not crash
    return Response.json(
      { translated: text, detectedLang: targetLang, error: String(err) },
      { status: 500 }
    );
  }
}
