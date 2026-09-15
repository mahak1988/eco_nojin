/** Voice ask page — voice-enabled AI advisory. */

import { useState, useCallback } from 'react';
import { Mic, MessageSquare } from 'lucide-react';
import { useBilingual } from '../../hooks/useBilingual';
import Seo from '../../components/ui/Seo';
import PageHeader from '../../components/sections/PageHeader';
import AdvisoryRunner from '../../components/dashboard/AdvisoryRunner';
import Reveal from '../../components/ui/Reveal';

export default function VoiceAskPage() {
  const { lang } = useBilingual();
  const isFa = lang === 'fa';
  const fallback = (persian: string, english: string) => (isFa ? persian : english);
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [mode, setMode] = useState<'text' | 'voice'>('text');

  const handleVoiceClick = useCallback(async () => {
    if (!navigator.mediaDevices?.getUserMedia) {
      alert(isFa ? 'مرورگر پشتیبانی از میکروفون نمی‌کند' : 'Browser does not support microphone');
      return;
    }

    try {
      if (isRecording) {
        setIsRecording(false);
      } else {
        setIsRecording(true);
        setMode('voice');
        if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
          const SRClass = (window as typeof window & { SpeechRecognition?: typeof SpeechRecognition; webkitSpeechRecognition?: typeof SpeechRecognition }).SpeechRecognition ||
            (window as typeof window & { webkitSpeechRecognition?: typeof SpeechRecognition }).webkitSpeechRecognition;
          if (!SRClass) return;
          const recognition = new SRClass();
          recognition.lang = 'fa-IR';
          recognition.interimResults = false;
          recognition.onresult = (event: SpeechRecognitionEvent) => {
            setTranscript(event.results[0][0].transcript);
            setIsRecording(false);
          };
          recognition.onerror = () => { setIsRecording(false); };
          recognition.start();
        }
      }
    } catch {
      setIsRecording(false);
    }
  }, [isRecording, isFa]);

  return (
    <>
      <Seo title={fallback('پرسش صوتی', 'Voice Ask')} path="/dashboard/voice-ask" />
      <PageHeader
        kicker={fallback('ابزارهای صوتی', 'Voice Tools')}
        title={fallback('پرسش صوتی', 'Voice Ask')}
        lead={fallback('سؤال کشاورزی خود را بگویید یا بنویسید — پاسخ با ارجاع به مستندات علمی.', 'Ask farming questions by voice or text — answers with scientific references.')}
      />

      <section className="px-4 py-12 sm:px-6" id="voice-ask">
        <div className="mx-auto flex max-w-4xl flex-col gap-8">
          <Reveal>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="glass rounded-2xl p-5 cursor-pointer hover:shadow-lg transition-shadow" onClick={() => setMode('text')}>
                <h3 className="text-sm font-extrabold text-[var(--color-night-100)] flex items-center gap-2">
                  <MessageSquare className="h-5 w-5 text-[var(--color-leaf-400)]" aria-hidden />
                  {fallback('حالت متنی', 'Text Mode')}
                </h3>
                <p className="text-xs text-[var(--color-night-200)]/60 mt-2">
                  {fallback('سؤال خود را تایپ کنید', 'Type your question')}
                </p>
                {mode === 'text' && <div className="mt-2 h-1 w-full bg-[var(--color-leaf-500)] rounded-full" />}
              </div>

              <div className="glass rounded-2xl p-5 cursor-pointer hover:shadow-lg transition-shadow" onClick={() => { setMode('voice'); handleVoiceClick(); }}>
                <h3 className="text-sm font-extrabold text-[var(--color-night-100)] flex items-center gap-2">
                  <Mic className={`h-5 w-5 ${isRecording ? 'text-red-400 animate-pulse' : 'text-[var(--color-leaf-400)]'}`} aria-hidden />
                  {fallback('حالت صوتی', 'Voice Mode')}
                </h3>
                <p className="text-xs text-[var(--color-night-200)]/60 mt-2">
                  {fallback('سؤال خود را بگویید', 'Speak your question')}
                </p>
                {mode === 'voice' && <div className="mt-2 h-1 w-full bg-[var(--color-leaf-500)] rounded-full" />}
              </div>
            </div>
          </Reveal>

          {mode === 'voice' && (
            <Reveal delay={0.1}>
              <div className="glass rounded-2xl p-5">
                <div className="flex items-center gap-3 mb-4">
                  <Mic className={`h-6 w-6 ${isRecording ? 'text-red-400 animate-pulse' : 'text-[var(--color-night-200)]/30'}`} aria-hidden />
                  <span className="text-sm font-bold text-[var(--color-night-100)]">
                    {fallback('در حال گوش دادن...', 'Listening...')}
                  </span>
                </div>
                {transcript && (
                  <div className="rounded-xl bg-white/5 p-3 text-sm text-[var(--color-night-100)] dir-ltr" dir="ltr">{transcript}</div>
                )}
              </div>
            </Reveal>
          )}

          <Reveal delay={0.15}>
            <AdvisoryRunner />
          </Reveal>
        </div>
      </section>
    </>
  );
}
