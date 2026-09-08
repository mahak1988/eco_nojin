import Seo from '../components/ui/Seo';
import LegalPage from '../components/sections/LegalPage';
import { useLang } from '../i18n/LanguageContext';

/** Terms of Use page. */
export default function TermsPage() {
  const { t } = useLang();
  return (
    <>
      <Seo
        title={`${t.terms.title} | ${t.brand.name}`}
        description={t.terms.lead}
        path="/terms"
      />
      <LegalPage content={t.terms} />
    </>
  );
}
