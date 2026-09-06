import { useState } from 'react';
import { Badge, Card, CardBody, Input } from '@eco/ui';
import { roleClasses } from '@eco/ui/tokens';
import { cn } from '@eco/utils';

type Article = {
  id: string;
  title: string;
  excerpt: string;
  category: 'carbon' | 'water' | 'soil' | 'climate' | 'satellite';
  readMinutes: number;
  author: string;
  date: string;
};

const ARTICLES: Article[] = [
  {
    id: 'swat-overview',
    title: 'SWAT+ watershed modeling primer',
    excerpt: 'Daily time-step hydrology, sediment, and nutrients on a sub-basin scale.',
    category: 'water',
    readMinutes: 8,
    author: 'تیم Eco Nojin',
    date: '۱۴۰۴/۱۰',
  },
  {
    id: 'rothc-soil',
    title: 'RothC and the SOC question',
    excerpt: 'How the 26.4-year Rothamsted carbon model helps quantify stock changes.',
    category: 'carbon',
    readMinutes: 6,
    author: 'دکتر م. رحیمی',
    date: '۱۴۰۴/۰۹',
  },
  {
    id: 'sentinel2-ndvi',
    title: 'Reading NDVI from Sentinel-2',
    excerpt: 'Practical cloud-masking and composite strategies for restoration monitoring.',
    category: 'satellite',
    readMinutes: 5,
    author: 'تیم Eco Nojin',
    date: '۱۴۰۴/۰۸',
  },
  {
    id: 'aquacrop-yield',
    title: 'AquaCrop yield estimation under deficit irrigation',
    excerpt: 'How the FAO model handles water-stress curves and biomass accumulation.',
    category: 'water',
    readMinutes: 7,
    author: 'مهندس س. کریمی',
    date: '۱۴۰۴/۰۷',
  },
  {
    id: 'verra-mrv',
    title: 'Verra VM0007: the gold standard for soil carbon',
    excerpt: 'Inside the methodology that powers ۷۰٪ of issued soil-carbon credits.',
    category: 'carbon',
    readMinutes: 9,
    author: 'تیم Eco Nojin',
    date: '۱۴۰۴/۰۶',
  },
  {
    id: 'rusle-erosion',
    title: 'RUSLE from theory to practice',
    excerpt: 'Translating R, K, LS, C, P into actionable slope-by-slope decisions.',
    category: 'soil',
    readMinutes: 6,
    author: 'تیم Eco Nojin',
    date: '۱۴۰۴/۰۵',
  },
];

const CATEGORY_LABELS: Record<Article['category'], { label: string; tone: 'brand' | 'sky' | 'leaf' | 'warning' | 'info' }> = {
  carbon: { label: 'کربن', tone: 'leaf' },
  water: { label: 'آب', tone: 'sky' },
  soil: { label: 'خاک', tone: 'brand' },
  climate: { label: 'اقلیم', tone: 'warning' },
  satellite: { label: 'ماهواره', tone: 'info' },
};

export function KnowledgePage() {
  const [filter, setFilter] = useState<'all' | Article['category']>('all');
  const [query, setQuery] = useState('');

  const filtered = ARTICLES.filter((a) => {
    if (filter !== 'all' && a.category !== filter) return false;
    if (query && !`${a.title} ${a.excerpt}`.toLowerCase().includes(query.toLowerCase())) return false;
    return true;
  });

  return (
    <>
      <section className="surface-hero border-b border-ink/10 py-16">
        <div className="mx-auto w-full max-w-content px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <Badge tone="brand" variant="soft" className="mx-auto">
              دانش‌نامه
            </Badge>
            <h1 className={cn('mt-3 text-balance md:text-5xl', roleClasses.display)}>
              پشتوانهٔ علمی اکو نُژین
            </h1>
            <p className="mt-4 text-balance text-base text-ink-muted md:text-lg">
              مقاله‌ها، راهنماها و توضیحات عملی از مدل‌های علمی پشت پلتفرم.
            </p>
          </div>
        </div>
      </section>

      <section className="py-12">
        <div className="mx-auto w-full max-w-content px-4 sm:px-6 lg:px-8">
          {/* Filter chips */}
          <div className="flex flex-wrap gap-2">
            {(['all', 'carbon', 'water', 'soil', 'climate', 'satellite'] as const).map((c) => {
              const meta = c === 'all' ? null : CATEGORY_LABELS[c];
              const label = c === 'all' ? 'همه' : meta?.label ?? c;
              return (
                <button
                  key={c}
                  type="button"
                  onClick={() => setFilter(c)}
                  className={cn(
                    'rounded-full border px-4 py-1.5 text-sm font-medium transition',
                    filter === c
                      ? 'border-transparent bg-gradient-brand text-white shadow-soft'
                      : 'border-ink/10 bg-surface-raised text-ink-muted hover:border-ink/20 hover:text-ink',
                  )}
                >
                  {label}
                </button>
              );
            })}

            <div className="ms-auto w-full sm:w-72">
              <Input
                placeholder="جست‌وجو..."
                value={query}
                onChange={(e) => setQuery((e.target as HTMLInputElement).value)}
              />
            </div>
          </div>

          {/* Article grid */}
          <div className="mt-8 grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {filtered.map((a) => (
              <ArticleCard key={a.id} article={a} />
            ))}
            {filtered.length === 0 && (
              <div className="col-span-full rounded-xl border border-dashed border-ink/15 bg-surface-muted/40 p-10 text-center">
                <p className="text-sm text-ink-muted">مقاله‌ای یافت نشد.</p>
              </div>
            )}
          </div>
        </div>
      </section>
    </>
  );
}

function ArticleCard({ article }: { article: Article }) {
  const tone = CATEGORY_LABELS[article.category]?.tone ?? 'neutral';
  return (
    <Card className="group h-full transition-all hover:-translate-y-1 hover:shadow-raised">
      <CardBody className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <Badge tone={tone} variant="soft">
            {CATEGORY_LABELS[article.category]?.label ?? article.category}
          </Badge>
          <span className="text-xs text-ink-muted">{article.readMinutes} دقیقه مطالعه</span>
        </div>
        <h3 className="text-balance text-lg font-semibold leading-snug">{article.title}</h3>
        <p className="text-sm leading-relaxed text-ink-muted">{article.excerpt}</p>
        <div className="mt-auto flex items-center justify-between border-t border-ink/5 pt-3 text-xs">
          <span className="font-medium text-ink-muted">{article.author}</span>
          <span className="text-ink-subtle">{article.date}</span>
        </div>
      </CardBody>
    </Card>
  );
}