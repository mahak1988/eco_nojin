import { useState } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { ExternalLink, Satellite, Leaf, Droplets, Wheat } from 'lucide-react';
import { useLang } from '../../i18n/LanguageContext';
import Reveal from '../ui/Reveal';
import type { ImpactProject } from '../../content/pages/impactcarbon';

type ProjectType = 'forest' | 'wetland' | 'agriculture';

const TYPE_COLORS: Record<ProjectType, string> = {
  forest: '#2fb36b',
  wetland: '#2a9bb5',
  agriculture: '#d49b3f',
};

const TYPE_ICONS: Record<ProjectType, React.ComponentType<{ className?: string }>> = {
  forest: Leaf,
  wetland: Droplets,
  agriculture: Wheat,
};

const TYPE_LABELS_FA: Record<ProjectType, string> = {
  forest: 'جنگل‌کاری',
  wetland: 'بازگرداندن تالاب',
  agriculture: 'کشاورزی پایدار',
};

const TYPE_LABELS_EN: Record<ProjectType, string> = {
  forest: 'Forest restoration',
  wetland: 'Wetland restoration',
  agriculture: 'Sustainable agriculture',
};

const STATUS_LABELS_FA: Record<string, string> = {
  planning: 'در برنامه',
  active: 'فعال',
  completed: 'تکمیل شده',
};

const STATUS_LABELS_EN: Record<string, string> = {
  planning: 'Planning',
  active: 'Active',
  completed: 'Completed',
};

interface TooltipProps {
  project: ImpactProject;
  visible: boolean;
}

function ProjectTooltip({ project, visible }: TooltipProps) {
  const { lang } = useLang();
  const typeLabels = lang === 'fa' ? TYPE_LABELS_FA : TYPE_LABELS_EN;
  const statusLabels = lang === 'fa' ? STATUS_LABELS_FA : STATUS_LABELS_EN;

  return (
    <motion.div
      className="absolute z-20 w-56 rounded-xl border border-[var(--color-leaf-500)]/30 bg-[var(--color-night-900)]/95 p-4 shadow-2xl backdrop-blur-sm"
      style={{
        left: `${project.lng}%`,
        top: `${project.lat}%`,
        transform: 'translate(-50%, -100%)',
        opacity: visible ? 1 : 0,
        y: visible ? 0 : 10,
      }}
      transition={{ duration: 0.2 }}
    >
      <h4 className="text-sm font-extrabold text-[var(--color-night-100)]">
        {project.name}
      </h4>
      <p className="mt-1 text-xs text-[var(--color-night-200)]/60">
        {typeLabels[project.type]}
      </p>
      <p className="text-xs text-[var(--color-aqua-300)]">
        {statusLabels[project.status]}
      </p>
      {project.ha ? (
        <p className="mt-1 text-xs text-[var(--color-night-200)]/50">
          {project.ha.toLocaleString(lang === 'fa' ? 'fa-IR' : 'en-US')} ha
        </p>
      ) : null}

      <a
        href={`https://apps.sentinel-hub.eu/eo-browser/?zoom=12&lat=${project.lat}&lng=${project.lng}`}
        target="_blank"
        rel="noopener noreferrer"
        className="mt-2 flex items-center gap-1 text-[10px] font-bold text-[var(--color-leaf-300)] hover:text-[var(--color-leaf-200)]"
      >
        {lang === 'fa' ? 'مشاهده در سنتینل هاب' : 'View on Sentinel Hub'}
        <ExternalLink className="h-3 w-3" />
      </a>
    </motion.div>
  );
}

/**
 * Satellite map with NDVI heatmap overlay (SVG) + project markers linked to Sentinel Hub.
 * Shows conceptual satellite view now; links to real data when available.
 */
export default function SatelliteMap() {
  const { t, lang } = useLang();
  const reduce = useReducedMotion();
  const [hovered, setHovered] = useState<ImpactProject | null>(null);
  const projects = t.impact.projects;

  return (
    <section className="px-4 py-12 sm:px-6">
      <Reveal className="mx-auto flex max-w-6xl flex-col gap-8">
        <div className="flex flex-col items-center text-center">
          <h2 className="text-2xl font-extrabold text-[var(--color-night-100)] sm:text-3xl">
            {t.impact.mapTitle}
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-7 text-[var(--color-night-200)]/60">
            {t.impact.mapNote}
          </p>
        </div>
      </Reveal>

      <Reveal delay={0.2}>
        <div className="relative mx-auto h-[480px] w-full max-w-5xl overflow-hidden rounded-3xl border border-[var(--color-leaf-500)]/20">
          {/* depth effect */}
          <div className="absolute inset-0 bg-gradient-to-b from-[var(--color-night-800)] via-[var(--color-night-800)] to-[var(--color-night-900)]" />

          {/* NDVI heatmap overlay (conceptual) */}
          <div
            className="absolute inset-0"
            style={{
              backgroundImage:
                lang === 'fa'
                  ? 'radial-gradient(circle at 35% 30%, rgba(47,179,107,0.25) 0%, transparent 50%), radial-gradient(circle at 70% 65%, rgba(126,226,168,0.18) 0%, transparent 50%), radial-gradient(circle at 85% 20%, rgba(42,155,181,0.15) 0%, transparent 50%)'
                  : 'radial-gradient(circle at 35% 30%, rgba(47,179,107,0.25) 0%, transparent 50%), radial-gradient(circle at 70% 65%, rgba(126,226,168,0.18) 0%, transparent 50%), radial-gradient(circle at 85% 20%, rgba(42,155,181,0.15) 0%, transparent 50%)',
              mixBlendMode: 'overlay',
              opacity: 0.6,
            }}
            aria-hidden
          />

          {/* grid lines (subtle) */}
          <svg className="absolute inset-0 h-full w-full" aria-hidden>
            {Array.from({ length: 10 }).map((_, i) => (
              <line
                key={`v-${i}`}
                x1={i * 10 + '%'}
                y1="0"
                x2={i * 10 + '%'}
                y2="100%"
                stroke="rgba(255,255,255,0.03)"
                strokeWidth="1"
              />
            ))}
            {Array.from({ length: 8 }).map((_, i) => (
              <line
                key={`h-${i}`}
                x1="0"
                y1={i * 12.5 + '%'}
                x2="100%"
                y2={i * 12.5 + '%'}
                stroke="rgba(255,255,255,0.03)"
                strokeWidth="1"
              />
            ))}
          </svg>

          {/* satellite icon overlay */}
          <motion.div
            className="absolute top-4 start-4 z-10 flex items-center gap-2 rounded-full bg-[var(--color-night-900)] px-3 py-1.5"
            animate={reduce ? undefined : { opacity: [0.4, 1, 0.4] }}
            transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
          >
            <Satellite className="h-4 w-4 text-[var(--color-aqua-500)]" />
            <span className="text-[10px] font-bold text-[var(--color-night-200)]/60">
              {lang === 'fa' ? 'در حالت مفهومی' : 'Conceptual view'}
            </span>
          </motion.div>

          {/* project markers */}
          <div className="absolute inset-0">
            {projects.map((project) => {
              // Map lat/lng to percentage within the mock map (Iran bounding box approximation)
              const mapX = ((project.lng - 44) / (64 - 44)) * 100;
              const mapY = 100 - ((project.lat - 25) / (40 - 25)) * 100;
              const TypeIcon = TYPE_ICONS[project.type];
              const color = TYPE_COLORS[project.type];

              return (
                <div
                  key={project.name}
                  className="absolute z-10 flex flex-col items-center"
                  style={{ left: `${mapX}%`, top: `${mapY}%`, transform: 'translate(-50%, -50%)' }}
                  onMouseEnter={() => setHovered(project)}
                  onMouseLeave={() => setHovered(null)}
                >
                  <motion.div
                    className="relative flex h-12 w-12 items-center justify-center rounded-full border-2 border-white/20"
                    style={{ background: color }}
                    whileHover={reduce ? undefined : { scale: 1.3 }}
                    transition={{ type: 'spring', stiffness: 400, damping: 20 }}
                  >
                    <TypeIcon className="h-5 w-5 text-[var(--color-night-950)]" />
                  </motion.div>

                  {hovered?.name === project.name && (
                    <ProjectTooltip project={project} visible={true} />
                  )}

                  {/* Sentinel Hub link on click */}
                  <a
                    href={`https://apps.sentinel-hub.eu/eo-browser/?zoom=12&lat=${project.lat}&lng=${project.lng}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="absolute -bottom-6 text-[9px] font-bold text-[var(--color-leaf-300)] opacity-0 transition-opacity hover:opacity-100"
                    aria-label={lang === 'fa' ? 'مشاهده در سنتینل هاب' : 'View on Sentinel Hub'}
                  >
                    <ExternalLink className="h-3 w-3" />
                  </a>
                </div>
              );
            })}
          </div>

          {/* legend */}
          <div className="absolute bottom-3 start-3 z-10 flex gap-3 rounded-xl bg-[var(--color-night-950)]/60 px-3 py-2 backdrop-blur-sm">
            {Object.entries(TYPE_LABELS_FA).map(([key]) => {
              const typeKey = key as ProjectType;
              return (
                <div key={key} className="flex items-center gap-1.5">
                  <div
                    className="h-3 w-3 rounded-full"
                    style={{ background: TYPE_COLORS[typeKey] }}
                    aria-hidden
                  />
                  <span className="text-[10px] font-bold text-[var(--color-night-200)]/60">
                    {lang === 'fa' ? TYPE_LABELS_FA[typeKey] : TYPE_LABELS_EN[typeKey]}
                  </span>
                </div>
              );
            })}
          </div>

          {/* Sentinel Hub attribution link */}
          <div className="absolute bottom-3 end-3 z-10 rounded-xl bg-[var(--color-night-950)]/60 px-3 py-2 backdrop-blur-sm">
            <span className="text-[10px] font-bold text-[var(--color-night-200)]/60">
              {lang === 'fa'
                ? 'ماهواره: سنتینل-۲ (کوپرنیکوس)'
                : 'Satellite: Sentinel-2 (Copernicus)'}
            </span>
          </div>
        </div>
      </Reveal>

      <Reveal delay={0.4}>
        <p className="mx-auto max-w-3xl text-center text-[10px] text-[var(--color-night-200)]/35">
          {lang === 'fa'
            ? 'نقشه شامل لایهٔ گرمایشی NDVI و مارکرهای پروژه است؛ هر مارکر لینک به Sentinel Hub EO Browser دارد.'
            : 'The map includes an NDVI heatmap layer and project markers; each marker links directly to Sentinel Hub EO Browser.'}
        </p>
      </Reveal>
    </section>
  );
}
