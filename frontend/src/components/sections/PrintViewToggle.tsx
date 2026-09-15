import { useLang } from '../../i18n/LanguageContext';

/** Print-friendly view toggle. */
export default function PrintViewToggle() {
  const { lang } = useLang();

  return (
    <button
      type="button"
      onClick={() => {
        if (document.querySelector('[data-print-only]')) {
          document.querySelector('[data-print-only]')!.remove();
          document.body.style.display = '';
        } else {
          const printDiv = document.createElement('div');
          printDiv.setAttribute('data-print-only', '');
          printDiv.className = 'fixed inset-0 z-[9999] bg-white p-8 text-black overflow-auto';
          printDiv.innerHTML = `<h1 style="font-size:24px;font-weight:bold;margin-bottom:16px">${lang === 'fa' ? 'گزارش پلتفرم Eco Nojin' : 'Eco Nojin Platform Report'}</h1><p style="color:#666;font-size:14px;margin-bottom:16px">${lang === 'fa' ? 'تاریخ: ' + new Date().toLocaleDateString('fa-IR') : 'Date: ' + new Date().toLocaleDateString()}</p>`;
          document.body.appendChild(printDiv);
          window.print();
          printDiv.remove();
        }
      }}
      className="rounded-xl glass p-2 text-[var(--color-night-200)]/40 hover:text-[var(--color-night-100)]"
      aria-label={lang === 'fa' ? 'پرینت' : 'Print'}
      title={lang === 'fa' ? 'پرینت' : 'Print'}
    >
      🖨️
    </button>
  );
}
