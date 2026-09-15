import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, Search, Filter, Leaf, Satellite, Layers, Droplets, Blocks, CloudSun, Coins, FlaskConical } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { useBilingual } from '../../hooks/useBilingual';
import Reveal from '../ui/Reveal';
import UniversalCard from '../ui/UniversalCard';
import type { CardTheme } from '../ui/UniversalCard';
import { categories as registryCategories, registry } from '../../lib/hydromaregistry';
import { Link } from 'react-router-dom';

const CATEGORY_CONFIG: Record<string, { theme: CardTheme; icon: LucideIcon }> = {
  indices: { theme: 'aqua', icon: Satellite },
  formulas: { theme: 'leaf', icon: FlaskConical },
  soil: { theme: 'sand', icon: Layers },
  hydro: { theme: 'aqua', icon: Droplets },
  simulation: { theme: 'leaf', icon: Blocks },
  carbon: { theme: 'sand', icon: Leaf },
  climate: { theme: 'aqua', icon: CloudSun },
  economics: { theme: 'leaf', icon: Coins },
};

/** Collapsible model category tree with UniversalCard-powered model entries. */
export default function CategoryTree() {
  const { fa } = useBilingual();
  const [openCategories, setOpenCategories] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const [showCalculatorsOnly, setShowCalculatorsOnly] = useState(false);

  const toggleCategory = (key: string) => {
    setOpenCategories((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const filteredRegistry = useMemo(() => {
    let entries = registry;

    if (showCalculatorsOnly) {
      entries = entries.filter((e) => e.impl === 'calculator' || e.impl === 'engine+calculator');
    }

    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      entries = entries.filter(
        (e) =>
          e.nameEn.toLowerCase().includes(q) ||
          e.nameFa.toLowerCase().includes(q) ||
          e.id.toLowerCase().includes(q) ||
          e.descEn.toLowerCase().includes(q) ||
          e.descFa.toLowerCase().includes(q),
      );
    }

    return entries;
  }, [showCalculatorsOnly, searchQuery]);

  const isOpenAll = () => openCategories.size === registryCategories.length;

  const toggleAll = () => {
    if (isOpenAll()) {
      setOpenCategories(new Set());
    } else {
      setOpenCategories(new Set(registryCategories.map((c) => c.key)));
    }
  };

  return (
    <div className="flex flex-col gap-4">
      {/* search + filter bar */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1">
          <input
            type="search"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder={fa('جستجوی مدل...', 'Search models...')}
            className="w-full rounded-2xl border border-white/10 bg-[var(--color-night-950)]/60 px-3 py-2 pl-9 text-sm text-[var(--color-night-100)] outline-none placeholder:text-[var(--color-night-200)]/40 focus:border-[var(--color-leaf-500)]/40"
          />
          <Search className="absolute start-2.5 top-2.5 h-4 w-4 text-[var(--color-night-200)]/40" />
        </div>

        <button
          type="button"
          onClick={() => setShowCalculatorsOnly((v) => !v)}
          className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-[10px] font-bold transition-all ${
            showCalculatorsOnly
              ? 'bg-[var(--color-aqua-500)]/20 text-[var(--color-aqua-300)]'
              : 'glass text-[var(--color-night-200)]/60 hover:text-[var(--color-night-100)]'
          }}`}
        >
          <Filter className="h-3 w-3" />
          {fa('محاسبه‌گرها', 'Calculators')}
        </button>

        <button
          type="button"
          onClick={toggleAll}
          className="rounded-full bg-white/5 px-3 py-1.5 text-[10px] font-bold text-[var(--color-night-200)]/40 hover:text-[var(--color-night-100)]"
        >
          {fa(
            isOpenAll() ? 'بستن همه' : 'باز کردن همه',
            isOpenAll() ? 'Collapse all' : 'Expand all'
          )}
        </button>
      </div>

      {/* category tree */}
      <div className="flex flex-col gap-3">
        {registryCategories.map((category) => {
          const entries = filteredRegistry.filter((e) => e.category === category.key);
          if (entries.length === 0 && searchQuery) return null;

          const isOpen = openCategories.has(category.key);
          const config = CATEGORY_CONFIG[category.key] || { theme: 'leaf' as CardTheme, icon: Layers };
          const IconComp = config.icon;

          return (
            <Reveal key={category.key} delay={0.1}>
              <div className="glass rounded-3xl p-4">
                <button
                  type="button"
                  onClick={() => toggleCategory(category.key)}
                  className="flex w-full items-center gap-3 text-start"
                >
                  <motion.span
                    animate={{ rotate: isOpen ? 180 : 0 }}
                    transition={{ duration: 0.3 }}
                    className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[var(--color-leaf-500)]/12 text-[var(--color-leaf-300)]"
                  >
                    <ChevronDown className="h-3 w-3" />
                  </motion.span>

                  <div className="flex-1">
                    <h3 className="text-sm font-extrabold text-[var(--color-night-100)]">
                      {fa(category.nameFa, category.nameEn)}
                    </h3>
                    <p className="text-[10px] text-[var(--color-night-200)]/40">
                      {entries.length} {fa('مدل', 'models')}
                    </p>
                  </div>

                  <span
                    className="flex h-7 w-7 items-center justify-center rounded-xl"
                    style={{ backgroundColor: 'rgba(47,179,107,0.1)', color: 'var(--color-leaf-300)' }}
                  >
                    <IconComp className="h-4 w-4" />
                  </span>
                </button>

                <AnimatePresence initial={false}>
                  {isOpen ? (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.3, ease: [0.22, 0.61, 0.36, 1] }}
                      className="overflow-hidden"
                    >
                      <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                        {entries.map((entry, entryIndex) => (
                          <Link
                            key={entry.id}
                            to={`/dashboard/models/${entry.id}`}
                            className="group"
                          >
                            <UniversalCard
                              title={fa(entry.nameFa, entry.nameEn)}
                              desc={fa(entry.descFa, entry.descEn)}
                              icon="flask"
                              iconColor={
                                config.theme === 'aqua'
                                  ? 'var(--color-aqua-500)'
                                  : config.theme === 'sand'
                                    ? 'var(--color-sand-500)'
                                    : 'var(--color-leaf-500)'
                              }
                              theme={config.theme}
                              index={entryIndex}
                              flipOnHover={true}
                              backContent={{
                                source: entry.enginePath,
                                method: entry.ref,
                                standard: entry.impl,
                                frequency: `${entries.length} models in category`,
                                apiField: entry.id,
                              }}
                            />
                          </Link>
                        ))}
                      </div>
                    </motion.div>
                  ) : null}
                </AnimatePresence>
              </div>
            </Reveal>
          );
        })}
      </div>
    </div>
  );
}
