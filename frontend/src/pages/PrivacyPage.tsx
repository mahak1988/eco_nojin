import Seo from '../components/ui/Seo';
import LegalPage from '../components/sections/LegalPage';
import { useLang } from '../i18n/LanguageContext';

/** Privacy policy page. */
export default function PrivacyPage() {
  const { t } = useLang();
  return (
    <>
      <Seo
        title={`${t.privacy.title} | ${t.brand.name}`}
        description={t.privacy.lead}
        path="/privacy"
      />
      <LegalPage content={t.privacy} />
    </>
  );
}
