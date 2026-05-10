import { NextRequest } from "next/server";
import OpenAI from "openai";

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

async function detectLang(text: string): Promise<string> {
  const res = await openai.chat.completions.create({
    model: "gpt-4o-mini",
    messages: [
      {
        role: "system",
        content:
          "Detect the language of the text. Reply with ONLY the ISO 639-1 code (e.g. 'de', 'hi', 'fr', 'en'). Nothing else.",
      },
      { role: "user", content: text },
    ],
    max_tokens: 5,
    temperature: 0,
  });
  return res.choices[0]?.message?.content?.trim().toLowerCase() ?? "en";
}

async function translate(text: string, targetLang: string): Promise<string> {
  const langName =
    new Intl.DisplayNames(["en"], { type: "language" }).of(targetLang) ?? targetLang;

  const res = await openai.chat.completions.create({
    model: "gpt-4o-mini",
    messages: [
      {
        role: "system",
        content: `You are a professional translator. Translate the following text to ${langName}. Return ONLY the translated text — preserve all line breaks, formatting, and structure exactly.`,
      },
      { role: "user", content: text },
    ],
    temperature: 0.1,
  });
  return res.choices[0]?.message?.content?.trim() ?? text;
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

    // When converting user input → English: detect language first
    if (targetLang === "en") {
      const detectedLang = await detectLang(text);
      if (detectedLang === "en") {
        // Already English — skip translation
        return Response.json({ translated: text, detectedLang: "en" });
      }
      const translated = await translate(text, "en");
      return Response.json({ translated, detectedLang });
    }

    // When converting backend response → user's language: no detection needed
    const translated = await translate(text, targetLang);
    return Response.json({ translated, detectedLang: targetLang });
  } catch (err) {
    console.error("[translate] error:", String(err));
    return Response.json(
      { translated: text, detectedLang: targetLang, error: String(err) },
      { status: 500 }
    );
  }
}
