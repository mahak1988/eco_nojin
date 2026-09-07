import { useTranslation } from 'react-i18next';
import { usePageTitle } from '@/app/usePageTitle';
import { Hero } from './sections/Hero';
import { ModelsShowcase } from './sections/ModelsShowcase';
import { GlobalStats } from './sections/GlobalStats';
import { TrustMarquee } from './sections/TrustMarquee';
import { LiveMapSection } from './sections/LiveMapSection';
import { CallToAction } from './sections/CallToAction';

export function HomePage() {
  const { t } = useTranslation();
  usePageTitle(t('home.docTitle', 'اکو نوجین — دوقلوی دیجیتال بازسازی سرزمین'));
  return (
    <>
      <Hero />
      <ModelsShowcase />
      <GlobalStats />
      <TrustMarquee />
      <LiveMapSection />
      <CallToAction />
    </>
  );
}
