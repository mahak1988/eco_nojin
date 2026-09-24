import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { StatusDot } from '@/components/StatusDot';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface Course {
  id: string;
  title: string;
  description: string;
  duration: string;
  level: 'beginner' | 'intermediate' | 'advanced';
  languages: string[];
  certified: boolean;
  enrolled: number;
  source: string;
}

const MOCK_COURSES: Course[] = [
  { id: 'c1', title: 'Introduction to HydroMa Models', description: 'Fundamentals of soil-water-carbon modeling', duration: '8 hours', level: 'beginner', languages: ['fa', 'en'], certified: true, enrolled: 1240, source: 'HydroMa Academy' },
  { id: 'c2', title: 'Advanced Carbon Accounting', description: 'IPCC Tier 2/3 methods for soil carbon', duration: '16 hours', level: 'advanced', languages: ['en', 'fr', 'es'], certified: true, enrolled: 342, source: 'Verra/GS' },
  { id: 'c3', title: 'Participatory GIS for Land Mapping', description: 'Community-based land use mapping with QGIS', duration: '12 hours', level: 'intermediate', languages: ['fa', 'en', 'ar', 'ur'], certified: false, enrolled: 890, source: 'OSGeo' },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'دوره‌های آموزشی', en: 'Courses' };
  const descriptions: Record<string, string> = { fa: 'کاتالوگ دوره‌های تخصصی با گواهی', en: 'Specialized courses catalog with certification' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/education/courses`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/education/courses`, languages: { fa: `${BASE_URL}/fa/public/education/courses`, en: `${BASE_URL}/en/public/education/courses` } },
  };
}

export default async function CoursesPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.education.courses');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Course Registry" label={t('provenanceLabel')} verified={true} method="Curated" timestamp="2024-12-10">
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
          evidence={['Expert-led content', 'Hands-on exercises', 'Certification pathways']}
          limits={['Limited advanced tracks', 'Lab access requires partnership', 'Certification renewal pending']}
          next={['Add micro-credentials', 'Enable offline sync', 'Partner with universities']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('catalog')}</h2>
        <div className="grid gap-4">
          {MOCK_COURSES.map(course => (
            <Card key={course.id} density="compact">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <h3 className="font-medium text-ink">{course.title}</h3>
                  <p className="text-sm text-ink-soft mt-1">{course.description}</p>
                  <div className="flex flex-wrap gap-2 mt-2 text-xs">
                    <span className="px-2 py-1 rounded bg-forest/10 text-forest">{course.level}</span>
                    <span className="px-2 py-1 rounded bg-clay/10 text-clay">{course.duration}</span>
                    {course.certified && <span className="px-2 py-1 rounded bg-amber/10 text-amber">{common('certified')}</span>}
                    <span className="px-2 py-1 rounded bg-slate/10 text-slate">{course.enrolled} {common('enrolled')}</span>
                  </div>
                </div>
                <ProvenanceStamp source={course.source} verified={course.certified} label={course.certified ? common('certified') : common('draft')} />
              </div>
            </Card>
          ))}
        </div>
      </section>
    </main>
  );
}