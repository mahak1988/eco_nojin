import Seo from '../components/ui/Seo';
import Hero from '../components/sections/Hero';
import CapabilityGrid from '../components/sections/CapabilityGrid';
import ScienceChain from '../components/sections/ScienceChain';
import ModelsMarquee from '../components/sections/ModelsMarquee';
import ChannelsGrid from '../components/sections/ChannelsGrid';
import CarbonBand from '../components/sections/CarbonBand';
import CtaBand from '../components/sections/CtaBand';
import { useLang } from '../i18n/LanguageContext';

/** Home v2 — six calm sections with φ rhythm (report 66): Hero (+slim stats),
 * Capabilities, Science chain + model ribbon, Channels, Carbon, CTA.
 * WhyBand and the standalone stats wall moved out of the fold. */
export default function HomePage() {
  const { t } = useLang();

  return (
    <>
      <Seo title={t.meta.title} description={t.meta.description} path="/" />
      <Hero />
      <CapabilityGrid />
      <ScienceChain variant="preview" />
      <ModelsMarquee />
      <ChannelsGrid />
      <CarbonBand />
      <CtaBand />
    </>
  );
}
