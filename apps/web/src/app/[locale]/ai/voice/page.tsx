'use client';

import { usePathname } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { useCallback, useEffect, useRef, useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';

const CHAT_PATH = '/api/v1/ai/chat';
const LANGUAGES_PATH = '/api/v1/voice/languages';

const SUPPORTED_LANGUAGES = new Set([
  'fa',
  'en',
  'ar',
  'ur',
  'de',
  'es',
  'fr',
  'hi',
  'it',
  'ms',
  'pt',
  'zh',
  'bn',
]);

type Voice = { code: string; name: string; voices: string[] };
type Message = { id: string; role: 'user' | 'assistant'; content: string };

interface SpeechRecognitionAlternativeLike {
  transcript: string;
}
interface SpeechRecognitionResultLike {
  isFinal: boolean;
  0: SpeechRecognitionAlternativeLike;
}
interface SpeechRecognitionEventLike extends Event {
  resultIndex: number;
  results: { length: number; [index: number]: SpeechRecognitionResultLike };
}
interface SpeechRecognitionErrorEventLike extends Event {
  error: string;
}
interface SpeechRecognitionLike extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start(): void;
  stop(): void;
  onend: (() => void) | null;
  onerror: ((event: SpeechRecognitionErrorEventLike) => void) | null;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
}

function readDetail(data: unknown, fallback: string): string {
  if (data && typeof data === 'object') {
    const record = data as Record<string, unknown>;
    if (typeof record.detail === 'string') return record.detail;
    if (record.detail !== undefined) return fallback;
  }
  if (typeof data === 'string' && data.trim()) return data;
  return fallback;
}

export default function VoicePage() {
  const t = useTranslations('ai');
  const common = useTranslations('common');
  const statusPage = useTranslations('statusPage');
  const statusLine = useTranslations('statusLine');
  const template = useTranslations('market.template');
  const pathname = usePathname();
  const locale = pathname.split('/')[1];

  const [languages, setLanguages] = useState<Voice[]>([]);
  const [languagesReachable, setLanguagesReachable] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState(locale);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let active = true;
    fetch(LANGUAGES_PATH, { credentials: 'same-origin', cache: 'no-store' })
      .then((res) => (res.ok ? res.json() : null))
      .then((data: unknown) => {
        if (!active || !data || typeof data !== 'object') return;
        const list = (data as { languages?: unknown }).languages;
        if (Array.isArray(list)) {
          setLanguages(list as Voice[]);
          setLanguagesReachable(true);
        }
      })
      .catch(() => undefined);
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (messages.length > 0) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const speak = useCallback(
    (text: string) => {
      if (typeof window === 'undefined' || !('speechSynthesis' in window)) return;
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = selectedLanguage;
      window.speechSynthesis.speak(utterance);
    },
    [selectedLanguage],
  );

  const ask = useCallback(
    async (text: string) => {
      const question = text.trim();
      if (!question) return;
      setMessages((previous) => [
        ...previous,
        { id: `u-${Date.now()}`, role: 'user', content: question },
      ]);
      setIsProcessing(true);
      setError(null);
      try {
        const res = await fetch(CHAT_PATH, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-CSRF-Intent': '1' },
          credentials: 'same-origin',
          body: JSON.stringify(
            SUPPORTED_LANGUAGES.has(selectedLanguage)
              ? { question, language: selectedLanguage }
              : { question },
          ),
        });
        const data: unknown = await res.json().catch(() => null);
        if (!res.ok) throw new Error(readDetail(data, common('error')));
        const payload = (data ?? {}) as Record<string, unknown>;
        const answer = typeof payload.answer === 'string' ? payload.answer : '';
        if (!answer) throw new Error(common('error'));
        setMessages((previous) => [
          ...previous,
          { id: `a-${Date.now()}`, role: 'assistant', content: answer },
        ]);
        speak(answer);
      } catch (err) {
        setError(err instanceof Error ? err.message : common('error'));
      } finally {
        setIsProcessing(false);
      }
    },
    [common, selectedLanguage, speak],
  );

  useEffect(() => {
    const scope = window as unknown as {
      SpeechRecognition?: new () => SpeechRecognitionLike;
      webkitSpeechRecognition?: new () => SpeechRecognitionLike;
    };
    const Recognition = scope.SpeechRecognition ?? scope.webkitSpeechRecognition;
    if (!Recognition) {
      setSpeechSupported(false);
      return;
    }

    const recognition = new Recognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = selectedLanguage;

    recognition.onend = () => setIsListening(false);
    recognition.onerror = (event) => {
      if (event.error !== 'no-speech') setError(`${statusPage('state')}: ${event.error}`);
      setIsListening(false);
    };
    recognition.onresult = (event) => {
      let transcript = '';
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        if (event.results[i].isFinal) transcript += event.results[i][0].transcript;
      }
      if (transcript) void ask(transcript);
    };

    recognitionRef.current = recognition;
    return () => {
      recognition.onend = null;
      recognition.onerror = null;
      recognition.onresult = null;
      recognition.stop();
    };
  }, [ask, selectedLanguage, statusPage]);

  const toggleListening = () => {
    const recognition = recognitionRef.current;
    if (!recognition) return;
    if (isListening) {
      recognition.stop();
    } else {
      setError(null);
      recognition.lang = selectedLanguage;
      recognition.start();
      setIsListening(true);
    }
  };

  return (
    <main id="main" className="min-h-dvh">
      <div className="mx-auto max-w-3xl px-6 pb-12 pt-8">
        <h1 className="display text-balance text-4xl font-bold text-ink">{t('title')}</h1>
        <p className="mt-3 max-w-2xl text-ink-soft">{t('lead')}</p>

        <div className="mt-4 flex flex-wrap items-center gap-3">
          <span className="chip num font-mono">{CHAT_PATH}</span>
          <span className="chip num font-mono">{LANGUAGES_PATH}</span>
        </div>

        {error && (
          <div className="mt-6 card border-clay/40 p-4 text-sm" role="alert">
            <p className="font-medium text-clay">{common('error')}</p>
            <p className="mt-1 text-ink-soft">{error}</p>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="mt-2"
              onClick={() => setError(null)}
            >
              {common('retry')}
            </Button>
          </div>
        )}

        <Card density="cozy" className="mt-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <h2 className="field-label">{statusPage('label')}</h2>
            <label htmlFor="voice-language" className="sr-only">
              {statusPage('label')}
            </label>
            <select
              id="voice-language"
              value={selectedLanguage}
              onChange={(event) => setSelectedLanguage(event.target.value)}
              className="rounded-md border border-line bg-background px-3 py-2 text-sm text-ink focus:outline-none focus:ring-2 focus:ring-forest"
              disabled={!languagesReachable}
            >
              {languagesReachable ? (
                languages.map((voice) => (
                  <option key={voice.code} value={voice.code}>
                    {voice.name} ({voice.voices.length})
                  </option>
                ))
              ) : (
                <option value={selectedLanguage}>{selectedLanguage}</option>
              )}
            </select>
          </div>
          <p className="mt-2 text-xs text-ink-soft">
            {languagesReachable ? statusLine('realData') : statusLine('unavailable')}
          </p>
        </Card>

        <Card density="cozy" className="mt-6 flex min-h-[320px] flex-col">
          <div className="flex-1 space-y-3" aria-live="polite">
            {messages.length === 0 && (
              <div className="py-8 text-center text-ink-soft">
                <p>{t('what')}</p>
              </div>
            )}
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm ${
                    message.role === 'user'
                      ? 'rounded-br-md bg-forest text-paper'
                      : 'rounded-bl-md border border-line bg-surface text-ink'
                  }`}
                >
                  {message.content}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        </Card>

        <div className="mt-6 flex flex-wrap items-center justify-center gap-4">
          <Button
            type="button"
            variant={isListening ? 'danger' : 'primary'}
            size="lg"
            onClick={toggleListening}
            disabled={!speechSupported || isProcessing}
            className="min-w-[180px]"
          >
            {isListening ? statusPage('state') : common('view')}
          </Button>
          <Button
            type="button"
            variant="secondary"
            size="lg"
            onClick={() => {
              const last = [...messages].reverse().find((message) => message.role === 'assistant');
              if (last) speak(last.content);
            }}
            disabled={messages.length === 0}
            className="min-w-[180px]"
          >
            {statusPage('result')}
          </Button>
        </div>

        <div className="mt-6 grid gap-3 md:grid-cols-2">
          <div className="rounded-md border border-line p-4">
            <h3 className="font-medium text-ink">{template('contractTitle')}</h3>
            <p className="mt-1 text-sm text-ink-soft">{template('contractDescription')}</p>
          </div>
          <div className="rounded-md border border-line p-4">
            <h3 className="font-medium text-ink">{template('nextTitle')}</h3>
            <p className="mt-1 text-sm text-ink-soft">{template('nextDescription')}</p>
          </div>
        </div>
      </div>
    </main>
  );
}
