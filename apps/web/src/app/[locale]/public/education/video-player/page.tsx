import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface Video {
  id: string;
  title: string;
  duration: string;
  languages: string[];
  subtitles: string[];
  source: string;
  views: number;
}

const MOCK_VIDEOS: Video[] = [
  { id: 'v1', title: 'HydroMa Engine Overview', duration: '12:34', languages: ['fa', 'en'], subtitles: ['fa', 'en', 'ar', 'es', 'fr'], source: 'HydroMa YouTube', views: 15420 },
  { id: 'v2', title: 'Setting Up Your First Land Profile', duration: '8:21', languages: ['fa', 'en', 'ur'], subtitles: ['fa', 'en', 'ar'], source: 'HydroMa Academy', views: 8930 },
  { id: 'v3', title: 'Carbon Registry Walkthrough', duration: '15:47', languages: ['en', 'fr', 'es', 'pt'], subtitles: ['en', 'fr', 'es', 'pt'], source: 'Verra Training', views: 4210 },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'پخش ویدئو', en: 'Video Player' };
  const descriptions: Record<string, string> = { fa: 'مجموعه ویدئوهای آموزشی با زیرنویس', en: 'Educational videos with subtitles' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/education/video-player`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/education/video-player`, languages: { fa: `${BASE_URL}/fa/public/education/video-player`, en: `${BASE_URL}/en/public/education/video-player` } },
  };
}

export default async function VideoPlayerPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.education.videoPlayer');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Video Registry" label={t('provenanceLabel')} verified={true} method="Curated" timestamp="2024-12-10">
          <h1 className="display text-4xl font-bold text-ink">{t('title')}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{t('lead')}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-6">
        <FivePart
          title={t('whatTitle')}
          lead={t('whatLead')}
          what={t('whatDesc')}
          audience={t('audience')}
          evidence={['Multi-language subtitles', 'Offline download support', 'Chapter markers']}
          limits={['Subtitle gaps for 12 locales', 'HD bandwidth requirements', 'Interactive transcripts pending']}
          next={['Add AI-generated subtitles', 'Enable variable playback', 'Link to course modules']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('videoCatalog')}</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {MOCK_VIDEOS.map(video => (
            <Card key={video.id} density="compact">
              <div className="aspect-video flex items-center justify-center bg-slate/10">
                <span className="text-4xl">▶</span>
              </div>
              <div className="mt-3">
                <h3 className="font-medium text-ink">{video.title}</h3>
                <p className="text-sm text-ink-soft mt-1">{video.duration} · {video.views.toLocaleString()} {common('views')}</p>
                <div className="flex flex-wrap gap-1 mt-2 text-xs">
                  {video.subtitles.map(lang => (
                    <span key={lang} className="px-1.5 py-0.5 rounded bg-forest/10 text-forest">{lang}</span>
                  ))}
                </div>
              </div>
              <div className="mt-2">
                <ProvenanceStamp source={video.source} verified={true} label={video.duration} />
              </div>
            </Card>
          ))}
        </div>
      </section>
    </main>
  );
}