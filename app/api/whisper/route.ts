import { NextRequest } from "next/server";

const LANG_NAME_TO_ISO: Record<string, string> = {
  afrikaans: "af", arabic: "ar", armenian: "hy", azerbaijani: "az",
  belarusian: "be", bosnian: "bs", bulgarian: "bg", catalan: "ca",
  chinese: "zh", croatian: "hr", czech: "cs", danish: "da",
  dutch: "nl", english: "en", estonian: "et", finnish: "fi",
  french: "fr", galician: "gl", german: "de", greek: "el",
  hebrew: "he", hindi: "hi", hungarian: "hu", icelandic: "is",
  indonesian: "id", italian: "it", japanese: "ja", kannada: "kn",
  kazakh: "kk", korean: "ko", latvian: "lv", lithuanian: "lt",
  macedonian: "mk", malay: "ms", marathi: "mr", nepali: "ne",
  norwegian: "no", persian: "fa", polish: "pl", portuguese: "pt",
  romanian: "ro", russian: "ru", serbian: "sr", slovak: "sk",
  slovenian: "sl", spanish: "es", swahili: "sw", swedish: "sv",
  tagalog: "tl", tamil: "ta", thai: "th", turkish: "tr",
  ukrainian: "uk", urdu: "ur", vietnamese: "vi", welsh: "cy",
};

export async function POST(request: NextRequest) {
  try {
    const apiKey = process.env.OPENAI_API_KEY;
    if (!apiKey) {
      return Response.json(
        { error: "OPENAI_API_KEY missing" },
        { status: 500 }
      );
    }

    const formData = await request.formData();
    const audio = formData.get("audio") as File | null;

    if (!audio) {
      return Response.json({ error: "No audio file provided" }, { status: 400 });
    }

    // Forward audio to OpenAI Whisper using multipart/form-data
    const body = new FormData();
    body.append("file", audio, audio.name || "recording.webm");
    body.append("model", "whisper-1");
    body.append("response_format", "verbose_json");

    const res = await fetch("https://api.openai.com/v1/audio/transcriptions", {
      method: "POST",
      headers: { Authorization: `Bearer ${apiKey}` },
      body,
    });

    if (!res.ok) {
      const errText = await res.text();
      console.error("[whisper] OpenAI error:", res.status, errText);
      return Response.json(
        { error: `OpenAI ${res.status}: ${errText}` },
        { status: 500 }
      );
    }

    const data = await res.json() as { text: string; language?: string };
    const langName = (data.language ?? "english").toLowerCase();
    const isoCode = LANG_NAME_TO_ISO[langName] ?? "en";

    return Response.json({ text: data.text, language: isoCode, languageName: langName });
  } catch (err) {
    console.error("[whisper] error:", String(err));
    return Response.json({ error: String(err) }, { status: 500 });
  }
}
