import Seo from '../components/ui/Seo';
import ScienceChain from '../components/sections/ScienceChain';
import OutputsList from '../components/sections/OutputsList';
import CtaBand from '../components/sections/CtaBand';
import { useLang } from '../i18n/LanguageContext';

/** HyDroMa science page: the full chain, core models, outputs and data sources. */
export default function HydromaPage() {
  const { t } = useLang();

  return (
    <>
      <Seo
        title={`${t.science.title} | ${t.brand.name}`}
        description={t.science.lead}
        path="/hydroma"
      />
      <ScienceChain variant="full" />
      <OutputsList />
      <CtaBand />
    </>
  );
}
