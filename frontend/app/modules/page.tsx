"use client";

import Link from "next/link";
import {
  Leaf, Satellite, Mountain, TrendingUp, ShoppingCart, TreePine,
  Droplet, Mic, Wallet, FlaskConical, CloudRain,
} from "lucide-react";
import { useI18n } from "@/lib/i18n-context";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PlatformPageHeader } from "@/components/site/PlatformPageHeader";
import { MotionSection } from "@/components/ui/motion-section";
import { LivingIcon } from "@/components/ui/living-icon";

const MODULES = [
  { key: "soil", href: "/modules/soil", icon: Leaf, color: "#f97316" },
  { key: "satellite", href: "/modules/satellite", icon: Satellite, color: "#0ea5e9" },
  { key: "erosion", href: "/modules/erosion", icon: Mountain, color: "#f59e0b" },
  { key: "scenarios", href: "/modules/scenarios", icon: TrendingUp, color: "#fbbf24" },
  { key: "marketplace", href: "/modules/marketplace", icon: ShoppingCart, color: "#fb7185" },
  { key: "carbon", href: "/modules/carbon", icon: TreePine, color: "#0d9488" },
  { key: "watershed", href: "/modules/watershed", icon: Droplet, color: "#38bdf8" },
  { key: "voice", href: "/modules/voice", icon: Mic, color: "#ec4899" },
  { key: "ecowallet", href: "/modules/ecowallet", icon: Wallet, color: "#8b5cf6" },
  { key: "analytics", href: "/modules/analytics", icon: FlaskConical, color: "#6366f1" },
  { key: "ai", href: "/modules/ai", icon: CloudRain, color: "#22c55e" },
];

export default function ModulesIndexPage() {
  const { t } = useI18n();
  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6" dir="rtl">
      <PlatformPageHeader
        eyebrow="مرکز ابزارهای HyDroMa"
        title="ماژول‌های تحلیلی"
        description="ابزارهای متصل به موتور علمی و سرویس‌های اکو نوژین برای خاک، آب، اقلیم، کربن، بازار و پایش مزرعه."
        actionHref="/dashboard"
        actionLabel="ورود به داشبورد"
      />
      <MotionSection className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {MODULES.map((m) => (
          <Link key={m.key} href={m.href} className="group transition-opacity hover:opacity-90">
            <Card className="h-full overflow-hidden transition duration-300 group-hover:-translate-y-1 group-hover:shadow-lg">
              <CardHeader className="flex flex-row items-center gap-3">
                <LivingIcon icon={m.icon} label={m.key} tone="green" className="h-11 w-11" />
                <CardTitle className="text-base">{t(`${m.key}_module_title`) ?? m.key}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  {t(`${m.key}_module_desc`) ?? "ورود به ماژول"}
                </p>
              </CardContent>
            </Card>
          </Link>
        ))}
      </MotionSection>
    </div>
  );
}
