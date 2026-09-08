/** Field gallery + conceptual NDVI sample chart for the impact page.
 * Visuals are generated (SVG) and clearly labelled — real field photos and
 * live data arrive with the pilot. */

import Reveal from '../ui/Reveal';
import { useLang } from '../../i18n/LanguageContext';

interface GalleryCard {
  title: string;
  desc: string;
  /** NDVI-style palette stops, low → high. */
  from: string;
  to: string;
  shape: 'circle' | 'strips' | 'terrace' | 'wetland';
}

const CARDS: GalleryCard[] = [
  { title: 'marginalLand', desc: 'marginalLandDesc', from: '#d49b3f', to: '#a3a13f', shape: 'strips' },
  { title: 'regenerated', desc: 'regeneratedDesc', from: '#7fb069', to: '#2fb36b', shape: 'circle' },
  { title: 'terrace', desc: 'terraceDesc', from: '#7fb069', to: '#177246', shape: 'terrace' },
  { title: 'wetland', desc: 'wetlandDesc', from: '#45bcd4', to: '#177246', shape: 'wetland' },
];

function FieldShape({ card }: { card: GalleryCard }) {
  const gid = `fg-${card.shape}`;
  return (
    <svg viewBox="0 0 200 120" className="h-full w-full" aria-hidden>
      <defs>
        <linearGradient id={gid} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor={card.from} />
          <stop offset="1" stopColor={card.to} />
        </linearGradient>
      </defs>
      <rect width="200" height="120" fill="#04100b" />
      {card.shape === 'circle' ? (
        <>
          <circle cx="100" cy="60" r="46" fill={`url(#${gid})`} opacity="0.9" />
          <circle cx="100" cy="60" r="30" fill="none" stroke="rgba(255,255,255,0.15)" />
        </>
      ) : null}
      {card.shape === 'strips' ? (
        <>
          <rect x="30" y="18" width="140" height="20" rx="6" fill={`url(#${gid})`} opacity="0.8" />
          <rect x="30" y="44" width="140" height="20" rx="6" fill={`url(#${gid})`} opacity="0.55" />
          <rect x="30" y="70" width="140" height="20" rx="6" fill={`url(#${gid})`} opacity="0.8" />
        </>
      ) : null}
      {card.shape === 'terrace' ? (
        <>
          <path d="M20 96 Q100 60 180 96 L180 110 L20 110 Z" fill={`url(#${gid})`} opacity="0.85" />
          <path d="M20 74 Q100 40 180 74 L180 88 L20 88 Z" fill={`url(#${gid})`} opacity="0.6" />
          <path d="M20 52 Q100 20 180 52 L180 66 L20 66 Z" fill={`url(#${gid})`} opacity="0.4" />
        </>
      ) : null}
      {card.shape === 'wetland' ? (
        <>
          <path d="M0 70 Q60 50 100 70 T200 70 L200 120 L0 120 Z" fill={`url(#${gid})`} opacity="0.8" />
          <path d="M0 82 Q60 62 100 82 T200 82" fill="none" stroke="#7fd8e8" strokeOpacity="0.6" />
          <circle cx="60" cy="40" r="14" fill="#45bcd4" opacity="0.4" />
          <circle cx="140" cy="34" r="10" fill="#45bcd4" opacity="0.3" />
        </>
      ) : null}
    </svg>
  );
}

/** Impact evidence gallery: conceptual field cards now, real pilot photos later. */
export default function FieldGallery() {
  const { lang } = useLang();

  const titles: Record<string, { title: string; desc: string }> = {
    marginalLand: {
      title: lang === 'fa' ? 'اراضی حاشیه‌ای' : 'Marginal land',
      desc:
        lang === 'fa'
          ? 'زمینِ کم‌بازده پیش از احیا؛ شناسایی با شاخص‌های ماهواره‌ای.'
          : 'Low-yield land before restoration; identified via satellite indices.',
    },
    regenerated: {
      title: lang === 'fa' ? 'مرعای احیا‌شده' : 'Regenerated rangeland',
      desc:
        lang === 'fa'
          ? 'پوشش گیاهی بازگشته پس از اقدام حفاظتی و پایش مستمر.'
          : 'Vegetation returned after conservation action and continuous monitoring.',
    },
    terrace: {
      title: lang === 'fa' ? 'تراس‌های حفاظتی' : 'Conservation terraces',
      desc:
        lang === 'fa'
          ? 'کاهش فرسایش با تراس‌بندی؛ سناریوی مدل‌شده با RUSLE.'
          : 'Erosion reduced by terracing; a scenario modelled with RUSLE.',
    },
    wetland: {
      title: lang === 'fa' ? 'تالاب بازگردانده' : 'Restored wetland',
      desc:
        lang === 'fa'
          ? 'بازگشت آب به تالاب و بهبود NDWI — هدف برنامهٔ احیا.'
          : 'Water returned to the wetland and NDWI improved — the restoration goal.',
    },
  };

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {CARDS.map((card, index) => (
        <Reveal key={card.title} delay={index * 0.06}>
          <figure className="glass glass-hover h-full overflow-hidden rounded-3xl">
            <div className="relative h-32 w-full">
              <FieldShape card={card} />
              <span className="absolute bottom-2 end-2 rounded-full bg-black/50 px-2.5 py-0.5 text-[10px] font-bold text-emerald-100/80">
                NDVI ▲
              </span>
            </div>
            <figcaption className="p-5">
              <h3 className="text-sm font-extrabold text-emerald-50">{titles[card.title].title}</h3>
              <p className="mt-1.5 text-xs leading-6 text-emerald-100/60">{titles[card.title].desc}</p>
            </figcaption>
          </figure>
        </Reveal>
      ))}
      <p className="col-span-full text-center text-[11px] text-emerald-100/35">
        {lang === 'fa'
          ? 'تصاویر بالا مفهومی و SVG هستند؛ عکس‌های واقعی میدان با نخستین پایلوت در همین گالری منتشر می‌شود.'
          : 'The visuals above are conceptual SVGs; real field photos will be published in this gallery with the first pilot.'}
      </p>
    </div>
  );
}
