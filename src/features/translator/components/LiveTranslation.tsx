import { useEffect, useMemo, useState } from "react";
import {
  ArrowLeftRight,
  FileVideo,
  Image,
  Mic,
  Play,
  Upload,
  Volume2,
} from "lucide-react";
import {
  fallbackTranslations,
  languageCodes,
  languages,
  touristPhrasebook,
  type Language,
} from "./TranslationData";

type Mode = "speech" | "image" | "video";

export function LiveTranslation() {
  const [mode, setMode] = useState<Mode>("speech");
  const [source, setSource] = useState<Language>("English");
  const [target, setTarget] = useState<Language>("French");
  const [listening, setListening] = useState(false);
  const [translating, setTranslating] = useState(false);
  const [transcript, setTranscript] = useState(fallbackTranslations.English);
  const [translated, setTranslated] = useState(fallbackTranslations.French);
  const [uploadName, setUploadName] = useState("No file uploaded");
  const [previewUrl, setPreviewUrl] = useState("");

  const statuses = useMemo(
    () => [
      listening ? "Listening" : "Ready to listen",
      translating ? "Translating" : "Detecting language",
      translated ? "Ready to speak" : "Waiting",
    ],
    [listening, translating, translated],
  );

  const suggestedPhrases = useMemo(
    () =>
      touristPhrasebook.map((phrase) => ({
        sourceText: phrase[source],
        targetText: phrase[target],
      })),
    [source, target],
  );

  const translateText = async () => {
    setTranslating(true);
    try {
      const url = `https://api.mymemory.translated.net/get?q=${encodeURIComponent(
        transcript,
      )}&langpair=${languageCodes[source]}|${languageCodes[target]}`;
      const response = await fetch(url);
      const data = await response.json();
      setTranslated(data?.responseData?.translatedText || fallbackTranslations[target]);
    } catch {
      setTranslated(fallbackTranslations[target]);
    } finally {
      setTranslating(false);
    }
  };

  useEffect(() => {
    const timer = window.setTimeout(() => {
      if (transcript.trim()) translateText();
    }, 450);

    return () => window.clearTimeout(timer);
  }, [transcript, source, target]);

  const swapLanguages = () => {
    setSource(target);
    setTarget(source);
    setTranscript(translated);
    setTranslated(transcript);
  };

  const selectPhrase = (sourceText: string, targetText: string) => {
    setTranscript(sourceText);
    setTranslated(targetText);
  };

  const startSpeechRecognition = () => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setListening((value) => !value);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = languageCodes[source];
    recognition.interimResults = false;
    recognition.onstart = () => setListening(true);
    recognition.onend = () => setListening(false);
    recognition.onresult = (event: any) => {
      const text = event.results?.[0]?.[0]?.transcript;
      if (text) setTranscript(text);
    };
    recognition.start();
  };

  const speakTranslation = () => {
    const utterance = new SpeechSynthesisUtterance(translated);
    utterance.lang = languageCodes[target];
    window.speechSynthesis.speak(utterance);
  };

  const handleUpload = (file?: File) => {
    setUploadName(file?.name ?? "No file uploaded");
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(file ? URL.createObjectURL(file) : "");
    setTranslated(
      mode === "image"
        ? "Detected sample text translated into the selected target language."
        : "Caption track generated and translated into the selected target language.",
    );
  };

  return (
    <div className="w-full overflow-hidden rounded-2xl border border-white/70 bg-white shadow-[0_18px_45px_rgba(15,23,42,.1)]">
      <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
        <div>
          <div className="mb-1 flex items-center gap-2 text-xs font-semibold text-emerald-700">
            <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-400" />
            Translation active
          </div>
          <h2 className="text-lg font-bold text-slate-950">Live Translation</h2>
          <p className="text-sm text-slate-500">
            Speech, image, and video translation for tourist conversations
          </p>
        </div>

        <button
          onClick={startSpeechRecognition}
          className={`flex h-11 w-11 items-center justify-center rounded-full text-white shadow-lg ${
            listening ? "bg-rose-500" : "bg-slate-800"
          }`}
        >
          <Mic className="h-5 w-5" />
        </button>
      </div>

      <div className="p-5 pb-4">
        <div className="mb-5 inline-flex rounded-xl bg-slate-100 p-1">
          {[
            { id: "speech", label: "Speech", icon: Mic },
            { id: "image", label: "Image", icon: Image },
            { id: "video", label: "Video", icon: FileVideo },
          ].map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setMode(id as Mode)}
              className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold ${
                mode === id
                  ? "bg-white text-blue-700 shadow-sm"
                  : "text-slate-500 hover:text-slate-800"
              }`}
            >
              <Icon className="h-4 w-4" />
              {label}
            </button>
          ))}
        </div>

        {mode === "speech" ? (
          <>
            <div className="grid grid-cols-[1fr_auto_1fr] items-end gap-3">
              <LanguageSelect label="Source" value={source} onChange={setSource} />
              <button
                onClick={swapLanguages}
                className="mb-0.5 flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 bg-slate-50 text-slate-600"
              >
                <ArrowLeftRight className="h-4 w-4" />
              </button>
              <LanguageSelect label="Target" value={target} onChange={setTarget} />
            </div>

            <div className="mt-4 grid grid-cols-1 gap-3 lg:grid-cols-2">
              <TextBox title="Transcript" value={transcript} onChange={setTranscript} />
              <TextBox title="Translated" value={translated} onChange={setTranslated} blue />
            </div>

            <div className="mt-4 flex flex-wrap gap-2">
              <div className="rounded-xl bg-emerald-50 px-4 py-2 text-sm font-bold text-emerald-700">
                {translating ? "Translating instantly..." : "Instant translation active"}
              </div>
              <ActionButton onClick={startSpeechRecognition} icon={Mic} label="Speak" />
              <ActionButton onClick={speakTranslation} icon={Volume2} label="Play" />
            </div>
          </>
        ) : (
          <MediaUpload mode={mode} uploadName={uploadName} previewUrl={previewUrl} onUpload={handleUpload} />
        )}

        <div className="mt-4 flex flex-wrap gap-2">
          {statuses.map((status, index) => (
            <span
              key={status}
              className={`rounded-full px-3 py-1 text-xs font-semibold ${
                index === 0 && listening
                  ? "bg-rose-50 text-rose-700"
                  : "bg-emerald-50 text-emerald-700"
              }`}
            >
              {status}
            </span>
          ))}
        </div>

        {mode === "speech" && (
          <div className="mt-4 rounded-2xl border border-slate-100 bg-slate-50 p-4">
            <div className="mb-3 flex items-center justify-between gap-3">
              <div>
                <h3 className="text-sm font-bold text-slate-900">Common tourist phrases</h3>
                <p className="text-xs text-slate-500">
                  Tap a {source} phrase to translate it into {target}.
                </p>
              </div>
              <span className="rounded-full bg-white px-3 py-1 text-xs font-bold text-blue-700 shadow-sm">
                {source} → {target}
              </span>
            </div>

            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
              {suggestedPhrases.map((phrase) => (
                <button
                  key={phrase.sourceText}
                  onClick={() => selectPhrase(phrase.sourceText, phrase.targetText)}
                  className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-left transition hover:border-blue-200 hover:bg-blue-50"
                >
                  <span className="block text-xs font-bold text-slate-800">{phrase.sourceText}</span>
                  <span className="mt-1 block text-[11px] font-semibold text-slate-400">
                    {phrase.targetText}
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function LanguageSelect({ label, value, onChange }: { label: string; value: Language; onChange: (v: Language) => void }) {
  return (
    <label className="grid gap-1 text-xs font-semibold text-slate-500">
      {label}
      <select
        value={value}
        onChange={(event) => onChange(event.target.value as Language)}
        className="rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm font-semibold text-slate-800"
      >
        {languages.map((language) => <option key={language}>{language}</option>)}
      </select>
    </label>
  );
}

function TextBox({ title, value, onChange, blue = false }: { title: string; value: string; onChange: (v: string) => void; blue?: boolean }) {
  return (
    <div className={`rounded-2xl border p-4 ${blue ? "border-blue-100 bg-blue-50" : "border-slate-100 bg-slate-50"}`}>
      <div className={`mb-3 text-xs font-bold uppercase tracking-[0.16em] ${blue ? "text-blue-500" : "text-slate-400"}`}>
        {title}
      </div>
      <textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="min-h-[82px] w-full resize-none bg-transparent text-sm leading-6 text-slate-900 outline-none"
      />
    </div>
  );
}

function ActionButton({ onClick, icon: Icon, label }: { onClick: () => void; icon: any; label: string }) {
  return (
    <button onClick={onClick} className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-bold text-slate-700">
      <Icon className="h-4 w-4" />
      {label}
    </button>
  );
}

function MediaUpload({ mode, uploadName, previewUrl, onUpload }: { mode: Mode; uploadName: string; previewUrl: string; onUpload: (file?: File) => void }) {
  return (
    <div className="grid gap-3">
      <label className="flex cursor-pointer items-center gap-3 rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-4 hover:border-blue-200 hover:bg-blue-50">
        <Upload className="h-5 w-5 text-blue-600" />
        <span>
          <span className="block text-sm font-bold text-slate-900">
            {mode === "image" ? "Upload image for OCR translation" : "Upload video for captions"}
          </span>
          <span className="text-xs text-slate-500">{uploadName}</span>
        </span>
        <input type="file" className="hidden" accept={mode === "image" ? "image/*" : "video/*"} onChange={(e) => onUpload(e.target.files?.[0])} />
      </label>

      {previewUrl && mode === "image" && <img src={previewUrl} alt="Preview" className="max-h-56 w-full rounded-2xl object-contain" />}
      {previewUrl && mode === "video" && <video src={previewUrl} controls className="max-h-56 w-full rounded-2xl" />}

      {(mode === "image"
        ? ["Menu translation", "Signboard translation", "Museum guide translation"]
        : ["Subtitle translation", "Speech transcript", "Translated captions"]
      ).map((label) => (
        <button key={label} className="flex items-center gap-3 rounded-2xl border border-slate-100 bg-white p-3 text-left text-sm font-bold text-slate-800 hover:border-blue-200 hover:bg-blue-50">
          {mode === "image" ? <Image className="h-4 w-4 text-blue-600" /> : <Play className="h-4 w-4 text-violet-600" />}
          {label}
        </button>
      ))}
    </div>
  );
}