import { LanguageMenu } from './LanguageMenu';

/**
 * Language selector for all public surfaces. Renders the 14-locale dropdown
 * menu (open/close, keyboard + outside-click dismiss).
 */
export function LocaleSwitcher({ current, label }: { current: string; label: string }) {
  return <LanguageMenu current={current} label={label} />;
}
