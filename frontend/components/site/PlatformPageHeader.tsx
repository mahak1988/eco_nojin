"use client";

import type { LucideIcon } from "lucide-react";
import { Activity, ArrowLeft, FlaskConical } from "lucide-react";
import Link from "next/link";
import { MotionSection } from "@/components/ui/motion-section";
import { MotionSticker } from "@/components/ui/motion-sticker";
import { LivingIcon } from "@/components/ui/living-icon";

interface PlatformPageHeaderProps {
  readonly eyebrow: string;
  readonly title: string;
  readonly description: string;
  readonly icon?: LucideIcon;
  readonly actionHref?: string;
  readonly actionLabel?: string;
}

export function PlatformPageHeader({
  eyebrow,
  title,
  description,
  icon: Icon = FlaskConical,
  actionHref,
  actionLabel,
}: PlatformPageHeaderProps) {
  return (
    <MotionSection className="relative overflow-hidden rounded-3xl border border-border bg-card/80 p-6 shadow-sm backdrop-blur sm:p-8">
      <div className="absolute -left-16 -top-20 h-48 w-48 rounded-full bg-emerald-500/10 blur-3xl" aria-hidden="true" />
      <div className="relative flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-4">
          <LivingIcon icon={Icon} label={eyebrow} tone="green" size={24} />
          <div>
            <MotionSticker label={eyebrow} icon={Activity} tone="blue" />
            <h1 className="mt-3 text-2xl font-bold tracking-tight text-foreground sm:text-3xl">{title}</h1>
            <p className="mt-2 max-w-3xl text-sm leading-7 text-muted-foreground sm:text-base">{description}</p>
          </div>
        </div>
        {actionHref && actionLabel ? (
          <Link
            href={actionHref}
            className="inline-flex shrink-0 items-center gap-2 rounded-xl border border-primary/30 px-4 py-2 text-sm font-semibold text-primary transition hover:-translate-y-0.5 hover:bg-primary/10"
          >
            {actionLabel}
            <ArrowLeft aria-hidden="true" size={16} />
          </Link>
        ) : null}
      </div>
    </MotionSection>
  );
}
