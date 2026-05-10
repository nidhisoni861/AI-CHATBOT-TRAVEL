"use client";

import { useRef, useState, useCallback } from "react";

// Maps ISO 639-1 codes → BCP-47 tags for speechSynthesis
const ISO_TO_BCP47: Record<string, string> = {
  af: "af-ZA", ar: "ar-SA", bg: "bg-BG", cs: "cs-CZ", da: "da-DK",
  de: "de-DE", el: "el-GR", en: "en-US", es: "es-ES", et: "et-EE",
  fi: "fi-FI", fr: "fr-FR", he: "he-IL", hi: "hi-IN", hr: "hr-HR",
  hu: "hu-HU", id: "id-ID", it: "it-IT", ja: "ja-JP", ko: "ko-KR",
  lt: "lt-LT", lv: "lv-LV", ms: "ms-MY", nl: "nl-NL", no: "nb-NO",
  pl: "pl-PL", pt: "pt-PT", ro: "ro-RO", ru: "ru-RU", sk: "sk-SK",
  sl: "sl-SI", sq: "sq-AL", sr: "sr-RS", sv: "sv-SE", sw: "sw-KE",
  ta: "ta-IN", th: "th-TH", tr: "tr-TR", uk: "uk-UA", ur: "ur-PK",
  vi: "vi-VN", zh: "zh-CN",
};

function getBCP47(isoCode: string) {
  return ISO_TO_BCP47[isoCode] ?? "en-US";
}

export function useVoice() {
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const voiceEnabledRef = useRef(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);

  const speak = useCallback((text: string, lang = "en") => {
    if (typeof window === "undefined" || !voiceEnabledRef.current) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = getBCP47(lang);
    utterance.rate = 0.95;
    utterance.pitch = 1;
    window.speechSynthesis.speak(utterance);
  }, []);

  const toggleVoice = useCallback(() => {
    const next = !voiceEnabledRef.current;
    voiceEnabledRef.current = next;
    setVoiceEnabled(next);
    if (!next && typeof window !== "undefined") {
      window.speechSynthesis.cancel();
    }
  }, []);

  const stopRecording = useCallback(() => {
    if (
      mediaRecorderRef.current &&
      mediaRecorderRef.current.state !== "inactive"
    ) {
      mediaRecorderRef.current.stop(); // triggers onstop → Whisper call
    }
    // Release the mic indicator light immediately
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
  }, []);

  const startRecording = useCallback(
    async (onResult: (transcript: string, detectedLang: string) => void) => {
      if (typeof window === "undefined") return;

      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        streamRef.current = stream;

        const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
          ? "audio/webm;codecs=opus"
          : "audio/webm";

        const recorder = new MediaRecorder(stream, { mimeType });
        chunksRef.current = [];

        recorder.ondataavailable = (e) => {
          if (e.data.size > 0) chunksRef.current.push(e.data);
        };

        recorder.onstop = async () => {
          const blob = new Blob(chunksRef.current, { type: mimeType });
          const file = new File([blob], "recording.webm", { type: mimeType });
          const formData = new FormData();
          formData.append("audio", file);

          try {
            const res = await fetch("/api/whisper", {
              method: "POST",
              body: formData,
            });
            const data = await res.json() as { text?: string; language?: string };
            onResult(data.text ?? "", data.language ?? "en");
          } catch {
            onResult("", "en");
          } finally {
            setIsRecording(false);
          }
        };

        mediaRecorderRef.current = recorder;
        recorder.start();
        setIsRecording(true);
      } catch {
        alert("Microphone access denied. Please allow it in your browser settings.");
        setIsRecording(false);
      }
    },
    []
  );

  const toggleRecording = useCallback(
    (onResult: (transcript: string, detectedLang: string) => void) => {
      if (isRecording) {
        stopRecording();
        // isRecording stays true until Whisper responds (onstop sets it to false)
      } else {
        startRecording(onResult);
      }
    },
    [isRecording, startRecording, stopRecording]
  );

  return { voiceEnabled, isRecording, speak, toggleVoice, toggleRecording };
}
