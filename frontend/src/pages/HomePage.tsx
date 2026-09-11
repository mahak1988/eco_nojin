import Seo from '../components/ui/Seo';
import Hero from '../components/sections/Hero';
import StatsBand from '../components/sections/StatsBand';
import WhyBand from '../components/sections/WhyBand';
import CapabilityGrid from '../components/sections/CapabilityGrid';
import ScienceChain from '../components/sections/ScienceChain';
import ModelsMarquee from '../components/sections/ModelsMarquee';
import ChannelsGrid from '../components/sections/ChannelsGrid';
import CarbonBand from '../components/sections/CarbonBand';
import CtaBand from '../components/sections/CtaBand';
import TrustBand from '../components/sections/TrustBand';
import { useLang } from '../i18n/LanguageContext';

/** Landing page: the full story in one scroll. */
export default function HomePage() {
  const { t } = useLang();

  return (
    <>
      <Seo title={t.meta.title} description={t.meta.description} path="/" />
      <Hero />
      <StatsBand />
      <WhyBand />
      <CapabilityGrid />
      <ScienceChain variant="preview" />
      <ModelsMarquee />
      <ChannelsGrid />
      <CarbonBand />
      <TrustBand />
      <CtaBand />
    </>
  );
}
