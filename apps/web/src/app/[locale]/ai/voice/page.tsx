'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { useTranslations } from 'next-intl';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';

interface VoiceMessage {
  id: string;
  type: 'user' | 'assistant' | 'system';
  text: string;
  timestamp: Date;
}

interface SpeechRecognitionEvent extends Event {
  resultIndex: number;
  results: SpeechRecognitionResultList;
}

interface SpeechRecognitionResultList {
  length: number;
  item(index: number): SpeechRecognitionResult;
  [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionResult {
  isFinal: boolean;
  length: number;
  item(index: number): SpeechRecognitionAlternative;
  [index: number]: SpeechRecognitionAlternative;
}

interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string;
  message: string;
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start(): void;
  stop(): void;
  onstart: ((this: SpeechRecognition, ev: Event) => void) | null;
  onend: ((this: SpeechRecognition, ev: Event) => void) | null;
  onerror: ((this: SpeechRecognition, ev: SpeechRecognitionErrorEvent) => void) | null;
  onresult: ((this: SpeechRecognition, ev: SpeechRecognitionEvent) => void) | null;
}

const SUPPORTED_LANGUAGES = [
  { code: 'fa', name: 'فارسی', nativeName: 'فارسی' },
  { code: 'en', name: 'English', nativeName: 'English' },
  { code: 'ar', name: 'العربية', nativeName: 'العربية' },
  { code: 'ur', name: 'اردو', nativeName: 'اردو' },
];

export default function VoicePage() {
  const t = useTranslations('ai.voice');
  const common = useTranslations('common');

  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [messages, setMessages] = useState<VoiceMessage[]>([]);
  const [selectedLanguage, setSelectedLanguage] = useState('fa');
  const [error, setError] = useState<string | null>(null);
  const [transcript, setTranscript] = useState('');

  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const synthesisRef = useRef<SpeechSynthesisUtterance | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      setError(t('unsupported'));
      return;
    }

    const SpeechRecognitionConstructor = (window as unknown as { SpeechRecognition: new () => SpeechRecognition; webkitSpeechRecognition: new () => SpeechRecognition }).SpeechRecognition ?? (window as unknown as { webkitSpeechRecognition: new () => SpeechRecognition }).webkitSpeechRecognition;
    const recognition = new SpeechRecognitionConstructor();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = selectedLanguage;

    recognition.onstart = () => {
      setIsListening(true);
      setError(null);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      if (event.error !== 'no-speech') {
        setError(t('recognitionError', { error: event.error }));
      }
      setIsListening(false);
    };

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let finalTranscript = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        }
      }
      if (finalTranscript) {
        setTranscript(finalTranscript);
        handleUserSpeech(finalTranscript);
      }
    };

    recognitionRef.current = recognition;

    return () => {
      recognition.stop();
    };
  }, [selectedLanguage, t]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleUserSpeech = useCallback(async (text: string) => {
    const userMessage: VoiceMessage = {
      id: Date.now().toString(),
      type: 'user',
      text,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsProcessing(true);

    try {
      const response = await fetch('/api/ai/voice', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, language: selectedLanguage }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error ?? t('error'));
      }

      const assistantMessage: VoiceMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        text: data.response,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);

      speakResponse(data.response);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('error'));
    } finally {
      setIsProcessing(false);
    }
  }, [selectedLanguage, t]);

  const speakResponse = (text: string) => {
    if (!('speechSynthesis' in window)) return;

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = selectedLanguage;
    utterance.rate = 1;
    utterance.pitch = 1;
    utterance.volume = 1;

    synthesisRef.current = utterance;
    window.speechSynthesis.speak(utterance);
  };

  const toggleListening = () => {
    if (!recognitionRef.current) return;

    if (isListening) {
      recognitionRef.current.stop();
    } else {
      setTranscript('');
      recognitionRef.current.lang = selectedLanguage;
      recognitionRef.current.start();
    }
  };

  const addSystemMessage = (text: string) => {
    const msg: VoiceMessage = {
      id: Date.now().toString(),
      type: 'system',
      text,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, msg]);
  };

  return (
    <main id="main" className="min-h-screen">
      <div className="mx-auto max-w-2xl px-4 py-8">
        <header className="mb-8">
          <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{t('title')}</h1>
          <p className="mt-2 text-ink-soft">{t('lead')}</p>
        </header>

        {error && (
          <div className="mb-6 p-4 rounded-md bg-red-50 border border-red-200 text-red-700" role="alert">
            {error}
            <Button variant="ghost" size="sm" className="ml-2" onClick={() => setError(null)}>
              Try again
            </Button>
          </div>
        )}

        <Card density="cozy" className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-medium text-ink">{t('languageLabel')}</h2>
            <select
              value={selectedLanguage}
              onChange={(e) => setSelectedLanguage(e.target.value)}
              className="px-3 py-2 rounded-md border border-line bg-background text-ink focus:outline-none focus:ring-2 focus:ring-forest"
              aria-label={t('languageLabel')}
            >
              {SUPPORTED_LANGUAGES.map((lang) => (
                <option key={lang.code} value={lang.code}>
                  {lang.nativeName} ({lang.name})
                </option>
              ))}
            </select>
          </div>
          <p className="text-sm text-ink-soft">{t('languageHint')}</p>
        </Card>

        <Card density="cozy" className="flex flex-col h-[calc(100vh-30rem)] min-h-[300px] mb-6">
          <div className="flex-1 overflow-y-auto p-4 space-y-3" aria-live="polite">
            {messages.length === 0 && (
              <div className="text-center text-ink-soft py-8">
                <p>{t('welcome')}</p>
              </div>
            )}
            {messages.map((msg) => (
              <div key={msg.id} className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`max-w-[85%] px-4 py-3 rounded-2xl text-sm ${
                    msg.type === 'user'
                      ? 'bg-forest text-paper rounded-br-md'
                      : msg.type === 'assistant'
                      ? 'bg-surface border border-line rounded-bl-md'
                      : 'bg-muted text-ink-soft rounded-md italic'
                  }`}
                >
                  {msg.text}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        </Card>

        <div className="flex items-center justify-center gap-4">
          <Button
            variant={isListening ? 'danger' : 'primary'}
            size="lg"
            onClick={toggleListening}
            disabled={isProcessing}
            aria-label={isListening ? t('stopListening') : t('startListening')}
            className="min-w-[160px]"
          >
            {isListening ? (
              <>
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" aria-hidden="true">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" fill="none" strokeLinecap="round" strokeDasharray="30 100" />
                </svg>
                {t('listening')}
              </>
            ) : (
              <>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                  <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z" />
                  <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                  <line x1="12" y1="19" x2="12" y2="22" />
                  <line x1="8" y1="22" x2="16" y2="22" />
                </svg>
                {t('startListening')}
              </>
            )}
          </Button>

          {isProcessing && (
            <Button variant="secondary" size="lg" disabled className="min-w-[160px]">
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" aria-hidden="true">
                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" fill="none" strokeLinecap="round" strokeDasharray="30 100" />
              </svg>
              {t('processing')}
            </Button>
          )}
        </div>

        <p className="mt-4 text-center text-xs text-ink-soft">{t('disclaimer')}</p>

        <Card density="compact" className="mt-6">
          <h3 className="font-medium text-ink mb-2">{t('commands')}</h3>
          <ul className="space-y-1 text-sm text-ink-soft">
            {t.raw('commandList')?.map((cmd: string, idx: number) => (
              <li key={idx} className="flex gap-2">
                <span className="text-forest">•</span>
                <span>{cmd}</span>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </main>
  );
}