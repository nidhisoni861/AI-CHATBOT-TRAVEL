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

async function translateOne(text: string, targetLang: string): Promise<string> {
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

// Batch: translate multiple short strings in one OpenAI call
async function translateBatch(texts: string[], targetLang: string): Promise<string[]> {
  if (!texts.length) return [];
  const langName =
    new Intl.DisplayNames(["en"], { type: "language" }).of(targetLang) ?? targetLang;

  const numbered = texts.map((t, i) => `${i + 1}: ${t}`).join("\n");

  const res = await openai.chat.completions.create({
    model: "gpt-4o-mini",
    messages: [
      {
        role: "system",
        content: `Translate each numbered item to ${langName}. Reply in the exact same numbered format (e.g. "1: translated text"). Translate ONLY the text after the colon. Keep proper nouns (city names, airline names) as-is.`,
      },
      { role: "user", content: numbered },
    ],
    temperature: 0.1,
  });

  const output = res.choices[0]?.message?.content ?? "";
  const lines = output.split("\n");

  return texts.map((original, i) => {
    const line = lines.find((l) => l.trim().startsWith(`${i + 1}:`));
    if (!line) return original;
    return line.replace(/^\d+:\s*/, "").trim();
  });
}

export async function POST(request: NextRequest) {
  let text = "";
  let targetLang = "en";

  try {
    const body = await request.json() as {
      text?: string;
      texts?: string[];
      targetLang?: string;
    };
    targetLang = body.targetLang ?? "en";

    // ── Batch mode: translate an array of strings ─────────────────────────────
    if (body.texts) {
      const translations = await translateBatch(body.texts, targetLang);
      return Response.json({ translations });
    }

    // ── Single mode ───────────────────────────────────────────────────────────
    text = body.text ?? "";
    if (!text.trim()) {
      return Response.json({ translated: text, detectedLang: targetLang });
    }

    if (targetLang === "en") {
      const detectedLang = await detectLang(text);
      if (detectedLang === "en") {
        return Response.json({ translated: text, detectedLang: "en" });
      }
      const translated = await translateOne(text, "en");
      return Response.json({ translated, detectedLang });
    }

    const translated = await translateOne(text, targetLang);
    return Response.json({ translated, detectedLang: targetLang });
  } catch (err) {
    console.error("[translate] error:", String(err));
    return Response.json(
      { translated: text, detectedLang: targetLang, translations: [], error: String(err) },
      { status: 500 }
    );
  }
}
