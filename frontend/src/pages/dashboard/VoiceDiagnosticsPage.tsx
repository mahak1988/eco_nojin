/** Voice diagnostics page — shows STT/TTS/IVR provider status. */

import { useState, useEffect, useCallback } from 'react';
import { useBilingual } from '../../hooks/useBilingual';
import Seo from '../../components/ui/Seo';
import PageHeader from '../../components/sections/PageHeader';
import Reveal from '../../components/ui/Reveal';
import SectionHeading from '../../components/ui/SectionHeading';
import { Mic, Speaker, Phone, Activity, Settings } from 'lucide-react';
import { getApiBase } from '../../lib/api';

interface ProviderStatus {
  provider: string;
  mode: string;
  features: Record<string, boolean>;
}

export default function VoiceDiagnosticsPage() {
  const { lang } = useBilingual();
  const isFa = lang === 'fa';
  const [sttStatus, setSttStatus] = useState<ProviderStatus | null>(null);
  const [ttsStatus, setTtsStatus] = useState<ProviderStatus | null>(null);
  const [ivrStatus, setIvrStatus] = useState<ProviderStatus | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchAll = useCallback(async () => {
    try {
      const [sttRes, ttsRes, ivrRes] = await Promise.all([
        fetch(`${getApiBase()}/api/v1/voice/diagnostics`),
        fetch(`${getApiBase()}/api/v1/voice/providers`),
        fetch(`${getApiBase()}/api/v1/voice/health`),
      ]);
      if (sttRes.ok) setSttStatus(await sttRes.json());
      if (ttsRes.ok) setTtsStatus(await ttsRes.json());
      if (ivrRes.ok) setIvrStatus(await ivrRes.json());
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  const fallback = (persian: string, english: string) => (isFa ? persian : english);

  return (
    <>
      <Seo title={fallback('صوتی تشخیص', 'Voice Diagnostics')} path="/dashboard/voice-diagnostics" />
      <PageHeader
        kicker={fallback('ابزارهای صوتی', 'Voice Tools')}
        title={fallback('تشخیص صدا', 'Voice Diagnostics')}
        lead={fallback('وضعیت موتورهای صوتی (STT/TTS/IVR) و تنظیمات فعال‌سازی.', 'Voice engine status and activation settings.')}
      />

      <section className="px-4 py-12 sm:px-6" id="voice-diagnostics">
        <div className="mx-auto flex max-w-4xl flex-col gap-8">
          <Reveal>
            <div className="mx-auto max-w-2xl text-center">
              <SectionHeading
                kicker={fallback('وضعیت سرویس‌ها', 'Service Status')}
                title={fallback('بررسی موتورها', 'Engine Check')}
                lead={fallback('وضعیت هر موتور صوتی و نحوه فعال‌سازی آن.', 'Each voice engine status and activation method.')}
              />
            </div>
          </Reveal>

          {loading ? (
            <div className="text-center py-12">
              <Activity className="h-8 w-8 mx-auto animate-spin text-[var(--color-leaf-400)]" aria-hidden />
              <p className="mt-3 text-sm text-[var(--color-night-200)]/50">{fallback('در حال بررسی...', 'Checking...')}</p>
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-3">
              <StatusCard
                icon={<Mic className="h-5 w-5" />}
                title={fallback('تشخیص گفتار', 'Speech Recognition')}
                status={sttStatus?.mode ?? 'unknown'}
                features={sttStatus?.features ?? {}}
              />
              <StatusCard
                icon={<Speaker className="h-5 w-5" />}
                title={fallback('تبدیل به گفتار', 'Text-to-Speech')}
                status={ttsStatus?.mode ?? 'unknown'}
                features={ttsStatus?.features ?? {}}
              />
              <StatusCard
                icon={<Phone className="h-5 w-5" />}
                title={fallback('IVR سیستم', 'IVR System')}
                status={ivrStatus?.features?.ivr_menu ? 'active' : 'mock'}
                features={ivrStatus?.features ?? {}}
              />
            </div>
          )}

          <Reveal delay={0.1}>
            <div className="glass rounded-2xl p-5">
              <h3 className="text-base font-extrabold text-[var(--color-night-100)] flex items-center gap-2">
                <Settings className="h-5 w-5 text-[var(--color-leaf-400)]" aria-hidden />
                {fallback('فعال‌سازی', 'Activation')}
              </h3>
              <p className="text-sm text-[var(--color-night-200)]/60 mt-2">
                {fallback(
                  'برای فعال‌سازی موتورهای واقعی، متغیرهای محیطی STT_PROVIDER و TTS_PROVIDER را تنظیم کنید. برای IVR تلفنی، Twilio اطلاعات (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN) را وارد کنید.',
                  'To activate real engines, set STT_PROVIDER and TTS_PROVIDER env variables. For telephony IVR, configure Twilio credentials.',
                )}
              </p>
              <code className="mt-3 block rounded-lg bg-black/5 p-3 text-[10px] dir-ltr text-left overflow-x-auto">
                {`STT_PROVIDER=whisper
TTS_PROVIDER=coqui
TWILIO_ACCOUNT_SID=your-sid
TWILIO_AUTH_TOKEN=your-token`}
              </code>
            </div>
          </Reveal>
        </div>
      </section>
    </>
  );
}

function StatusCard({
  icon,
  title,
  status,
  features,
}: {
  icon: React.ReactNode;
  title: string;
  status: string;
  features: Record<string, boolean>;
}) {
  return (
    <div className="glass rounded-2xl p-5">
      <div className="flex items-center gap-2 mb-3">
        {icon}
        <h4 className="text-sm font-extrabold text-[var(--color-night-100)]">{title}</h4>
      </div>
      <div className="flex items-center gap-2 mb-3">
        <span className={`h-2.5 w-2.5 rounded-full ${status === 'active' || status === 'operational' ? 'bg-green-400' : status === 'error' ? 'bg-red-400' : 'bg-yellow-400'}`} />
        <span className="text-xs font-bold text-[var(--color-night-200)]/60">{status}</span>
      </div>
      <div className="flex flex-wrap gap-1.5">
        {Object.entries(features).map(([key, value]) => (
          <span
            key={key}
            className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${value ? 'bg-[var(--color-leaf-500)]/15 text-[var(--color-leaf-400)]' : 'bg-gray-100 text-gray-400'}`}
          >
            {key}: {value ? '✓' : '✗'}
          </span>
        ))}
      </div>
    </div>
  );
}
