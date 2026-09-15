import { LanguageProvider } from '../i18n/LanguageContext';
import HomePage from './HomePage';

export default function HomeIsland() {
  return (
    <LanguageProvider>
      <HomePage />
    </LanguageProvider>
  );
}
