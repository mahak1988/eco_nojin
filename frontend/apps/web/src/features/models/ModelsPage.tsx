import { useEffect, useMemo, useState } from 'react';
import { loadStaticCatalog, listModels, TOTAL_BACKEND_MODELS, type ModelMeta } from '@eco/models';
import { Badge, Card, CardBody, Input } from '@eco/ui';
import { roleClasses } from '@eco/ui/tokens';
import { cn } from '@eco/utils';

type Domain = ModelMeta['domain'] | 'all';

const DOMAINS: { id: Domain; label: string; tone: 'brand' | 'sky' | 'leaf' | 'warning' | 'info' }[] = [
  { id: 'all', label: 'همه', tone: 'brand' },
  { id: 'water', label: '💧 آب', tone: 'sky' },
  { id: 'carbon', label: '🌱 کربن', tone: 'leaf' },
  { id: 'soil', label: '🌍 خاک', tone: 'brand' },
  { id: 'crop', label: '🌾 محصول', tone: 'leaf' },
  { id: 'climate', label: '🌤️ اقلیم', tone: 'warning' },
  { id: 'erosion', label: '⛰️ فرسایش', tone: 'brand' },
  { id: 'hydraulic', label: '🌊 هیدرولیک', tone: 'sky' },
  { id: 'optimization', label: '🎯 بهینه‌سازی', tone: 'info' },
];

export function ModelsPage() {
  useEffect(() => {
    loadStaticCatalog();
  }, []);

  const [domain, setDomain] = useState<Domain>('all');
  const [query, setQuery] = useState('');

  const allModels = listModels();

  const filtered = useMemo(() => {
    return allModels.filter((m) => {
      if (domain !== 'all' && m.domain !== domain) return false;
      if (query && !`${m.name} ${m.description}`.toLowerCase().includes(query.toLowerCase())) return false;
      return true;
    });
  }, [allModels, domain, query]);

  return (
    <>
      <section className="surface-hero border-b border-ink/10 py-16">
        <div className="mx-auto w-full max-w-content px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-3xl text-center">
            <Badge tone="brand" variant="soft" className="mx-auto">
              کاتالوگ مدل‌ها
            </Badge>
            <h1 className={cn('mt-3 text-balance md:text-5xl', roleClasses.display)}>
              {TOTAL_BACKEND_MODELS} مدل علمی در {allModels.length > 0 ? '۹' : '۱۴'} دامنه
            </h1>
            <p className="mt-4 text-balance text-base text-ink-muted md:text-lg">
              از SWAT+ تا RothC، از AquaCrop تا HEC-RAS. مرور، فیلتر و اجرا.
            </p>
          </div>
        </div>
      </section>

      <section className="py-12">
        <div className="mx-auto w-full max-w-content px-4 sm:px-6 lg:px-8">
          <div className="flex flex-wrap gap-2">
            {DOMAINS.map((d) => (
              <button
                key={d.id}
                type="button"
                onClick={() => setDomain(d.id)}
                className={cn(
                  'rounded-full border px-4 py-1.5 text-sm font-medium transition',
                  domain === d.id
                    ? 'border-transparent bg-gradient-brand text-white shadow-soft'
                    : 'border-ink/10 bg-surface-raised text-ink-muted hover:border-ink/20 hover:text-ink',
                )}
              >
                {d.label}
              </button>
            ))}
            <div className="ms-auto w-full sm:w-72">
              <Input
                placeholder="جست‌وجو..."
                value={query}
                onChange={(e) => setQuery((e.target as HTMLInputElement).value)}
              />
            </div>
          </div>

          <p className="mt-6 text-sm text-ink-muted">
            نمایش <span className="font-semibold text-ink">{filtered.length}</span> مدل از {allModels.length}.
          </p>

          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {filtered.map((m) => (
              <ModelCard key={m.id} model={m} />
            ))}
            {filtered.length === 0 && (
              <div className="col-span-full rounded-xl border border-dashed border-ink/15 bg-surface-muted/40 p-10 text-center">
                <p className="text-sm text-ink-muted">مدلی یافت نشد.</p>
              </div>
            )}
          </div>
        </div>
      </section>
    </>
  );
}

function ModelCard({ model }: { model: ModelMeta }) {
  return (
    <Card className="group flex h-full flex-col transition-all hover:-translate-y-1 hover:shadow-raised">
      <CardBody className="flex flex-1 flex-col gap-3">
        <div className="flex items-center justify-between">
          <Badge tone="brand" variant="soft">{model.domain}</Badge>
          <span className="rounded-full border border-ink/10 px-2 py-0.5 text-[10px] uppercase tracking-wider text-ink-muted">
            v{model.version}
          </span>
        </div>
        <h3 className="text-base font-semibold leading-snug">{model.name}</h3>
        <p className="text-sm leading-relaxed text-ink-muted">{model.description}</p>
        <dl className="mt-auto grid grid-cols-2 gap-2 border-t border-ink/5 pt-3 text-xs">
          <div>
            <dt className="text-ink-muted">منبع</dt>
            <dd className="font-medium">{model.source}</dd>
          </div>
          <div>
            <dt className="text-ink-muted">زمان</dt>
            <dd className="font-medium">{model.avg_runtime_ms} ms</dd>
          </div>
        </dl>
      </CardBody>
    </Card>
  );
}