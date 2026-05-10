"use client";

import { useRef, useState, useCallback } from "react";

// ISO 639-1 → BCP-47 for SpeechRecognition and SpeechSynthesis
const LANG_BCP47: Record<string, string> = {
  en: "en-US", de: "de-DE", hi: "hi-IN", fr: "fr-FR",
  es: "es-ES", it: "it-IT", pt: "pt-PT", nl: "nl-NL",
  ru: "ru-RU", zh: "zh-CN", ja: "ja-JP", ko: "ko-KR",
  ar: "ar-SA", pl: "pl-PL", tr: "tr-TR", sv: "sv-SE",
  da: "da-DK", fi: "fi-FI", no: "nb-NO", cs: "cs-CZ",
};

function toBCP47(lang: string): string {
  return LANG_BCP47[lang] ?? lang;
}

export function useVoice() {
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [isRecording, setIsRecording] = useState(false);
  const voiceEnabledRef = useRef(true);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const recognitionRef = useRef<any>(null);
  // Updated after each message so the next voice recording uses the correct language
  const recordingLangRef = useRef<string>(
    typeof navigator !== "undefined" ? navigator.language : "en-US"
  );

  const speak = useCallback((text: string, lang = "en") => {
    if (typeof window === "undefined" || !voiceEnabledRef.current) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = toBCP47(lang);
    utterance.rate = 0.95;
    utterance.pitch = 1;
    window.speechSynthesis.speak(utterance);
  }, []);

  const stopRecording = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }
    setIsRecording(false);
  }, []);

  const toggleVoice = useCallback(() => {
    const next = !voiceEnabledRef.current;
    voiceEnabledRef.current = next;
    setVoiceEnabled(next);
    if (!next && typeof window !== "undefined") {
      window.speechSynthesis.cancel();
      stopRecording();
    }
  }, [stopRecording]);

  const startRecording = useCallback((onResult: (text: string) => void) => {
    if (typeof window === "undefined") return;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) {
      alert("Speech recognition is not supported in this browser. Try Chrome.");
      return;
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const recognition: any = new SR();
    recognition.continuous = false;
    recognition.interimResults = false;
    // Use last detected language so recognition matches what the user speaks
    recognition.lang = recordingLangRef.current;

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    recognition.onresult = (e: any) => {
      const transcript: string = e.results[0][0].transcript;
      onResult(transcript);
      setIsRecording(false);
      recognitionRef.current = null;
    };
    recognition.onerror = () => {
      setIsRecording(false);
      recognitionRef.current = null;
    };
    recognition.onend = () => {
      setIsRecording(false);
      recognitionRef.current = null;
    };

    recognitionRef.current = recognition;
    recognition.start();
    setIsRecording(true);
  }, []);

  const toggleRecording = useCallback(
    (onResult: (text: string) => void) => {
      if (isRecording) {
        stopRecording();
      } else {
        startRecording(onResult);
      }
    },
    [isRecording, startRecording, stopRecording]
  );

  // Called after language is detected so next voice input uses the right lang
  const setRecordingLang = useCallback((lang: string) => {
    recordingLangRef.current = toBCP47(lang);
  }, []);

  return { voiceEnabled, isRecording, speak, toggleVoice, toggleRecording, setRecordingLang };
}
