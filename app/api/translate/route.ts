import { NextRequest } from "next/server";
import OpenAI from "openai";

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

async function detectLanguage(text: string): Promise<string> {
  const response = await openai.chat.completions.create({
    model: "gpt-4o-mini",
    messages: [
      {
        role: "system",
        content:
          "Detect the language of the given text. Reply with ONLY the ISO 639-1 language code (e.g. 'de', 'hi', 'fr', 'en'). Nothing else.",
      },
      { role: "user", content: text },
    ],
    max_tokens: 5,
    temperature: 0,
  });
  return response.choices[0]?.message?.content?.trim().toLowerCase() ?? "en";
}

async function translateText(
  text: string,
  targetLang: string,
  sourceLang?: string
): Promise<string> {
  const langName = new Intl.DisplayNames(["en"], { type: "language" }).of(targetLang) ?? targetLang;
  const systemPrompt = sourceLang
    ? `You are a professional translator. Translate the following text to ${langName}. Return ONLY the translated text, preserving all formatting, line breaks, and structure exactly.`
    : `You are a professional translator. Translate the following text to ${langName}. Return ONLY the translated text, preserving all formatting, line breaks, and structure exactly.`;

  const response = await openai.chat.completions.create({
    model: "gpt-4o-mini",
    messages: [
      { role: "system", content: systemPrompt },
      { role: "user", content: text },
    ],
    temperature: 0.1,
  });

  return response.choices[0]?.message?.content?.trim() ?? text;
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

    // Detect language first (only when translating to English, i.e. user input)
    let detectedLang = targetLang;
    if (targetLang === "en") {
      detectedLang = await detectLanguage(text);
      // If already English, skip translation
      if (detectedLang === "en") {
        return Response.json({ translated: text, detectedLang: "en" });
      }
    }

    const translated = await translateText(text, targetLang);
    return Response.json({ translated, detectedLang });
  } catch (err) {
    console.error("[translate] error:", String(err));
    return Response.json(
      { translated: text, detectedLang: targetLang, error: String(err) },
      { status: 500 }
    );
  }
}
