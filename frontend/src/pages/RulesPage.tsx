import Seo from '../components/ui/Seo';
import LegalPage from '../components/sections/LegalPage';
import { useLang } from '../i18n/LanguageContext';

/** Platform rules & regulations page. */
export default function RulesPage() {
  const { t } = useLang();
  return (
    <>
      <Seo
        title={`${t.rules.title} | ${t.brand.name}`}
        description={t.rules.lead}
        path="/rules"
      />
      <LegalPage content={t.rules} />
    </>
  );
}
