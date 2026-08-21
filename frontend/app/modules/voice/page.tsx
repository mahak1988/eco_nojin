'use client';
import { useState } from 'react';
import Footer from '../../../components/layout/Footer';
import { useI18n } from '../../../lib/i18n-context';
import { useTheme } from '../../../lib/theme-context';
import { motion } from 'framer-motion';
import { Mic, Volume2, Send } from 'lucide-react';
import { api, API_BASE } from '../../../lib/api-client';
import { LoadingState, ErrorState } from '../../../components/shared/ApiState';

export default function VoiceModulePage() {
  const { t, direction } = useI18n();
  const { colors } = useTheme();
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState<string | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const ask = async () => {
    if (!question.trim()) return;
    setLoading(true);
    setError(null);
    setAnswer(null);
    setAudioUrl(null);

    const res = await api.post<any>('/api/v1/voice/ask', { question, language: 'en' });
    if (res.success) {
      setAnswer(res.data?.answer || res.data?.text || '');
      if (res.data?.audio_url) {
        setAudioUrl(`${API_BASE}${res.data.audio_url}`);
      }
    } else {
      setError(res.error || 'Failed');
    }
    setLoading(false);
  };

  const speak = async () => {
    if (!answer) return;
    setLoading(true);
    const res = await api.post<any>('/api/v1/voice/tts', { text: answer, language: 'en' });
    if (res.success && res.data?.audio_url) {
      setAudioUrl(`${API_BASE}${res.data.audio_url}`);
    }
    setLoading(false);
  };

  return (
    <div dir={direction} style={{ background: colors.bg, minHeight: '100vh' }}>
      <div style={{ maxWidth: '900px', margin: '0 auto', padding: '40px 20px' }}>
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          style={{
            background: 'linear-gradient(135deg, #ec4899, #db2777)',
            padding: '40px', borderRadius: '20px', color: 'white', marginBottom: '32px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <Mic size={40} />
            <div>
              <h1 style={{ fontSize: '2rem', fontWeight: '800', margin: 0 }}>{t('module_voice')}</h1>
              <p style={{ margin: '4px 0 0', opacity: 0.95 }}>{t('module_voice_desc')}</p>
            </div>
          </div>
        </motion.div>

        <div style={{ background: colors.cardBg, padding: '24px', borderRadius: '16px', border: `1px solid ${colors.border}`, marginBottom: '24px' }}>
          <div style={{ display: 'flex', gap: '8px' }}>
            <input value={question} onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && ask()}
              aria-label={t('voice_ask_placeholder')} placeholder={t('voice_ask_placeholder')}
              style={{ flex: 1, padding: '14px', borderRadius: '12px', border: `1px solid ${colors.border}`, background: colors.bg, color: colors.text }} />
            <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
              onClick={ask} disabled={loading}
              style={{ padding: '14px 24px', background: 'linear-gradient(135deg, #ec4899, #db2777)', color: 'white', border: 'none', borderRadius: '12px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Send size={18} /> Ask
            </motion.button>
          </div>
        </div>

        {loading && <LoadingState message="Processing voice..." />}
        {error && <ErrorState message={error} />}
        {answer && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
            style={{ background: colors.cardBg, padding: '24px', borderRadius: '16px', border: `1px solid ${colors.border}` }}>
            <h3 style={{ marginBottom: '12px', color: colors.text }}>💬 Response</h3>
            <p style={{ color: colors.text, lineHeight: 1.7, marginBottom: '16px' }}>{answer}</p>
            <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
              <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
                onClick={speak}
                style={{ padding: '10px 20px', background: colors.primary, color: 'white', border: 'none', borderRadius: '10px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Volume2 size={16} /> Speak
              </motion.button>
              {audioUrl && <audio controls src={audioUrl} style={{ flex: 1 }} />}
            </div>
          </motion.div>
        )}
      </div>
      <Footer />
    </div>
  );
}
