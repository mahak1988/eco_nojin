"use client";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { Activity } from "lucide-react";
import { LivingIcon } from "@/components/ui/living-icon";
import { MotionSection } from "@/components/ui/motion-section";

interface ChartCardProps {
  title: string;
  description?: string;
  className?: string;
  children: React.ReactNode;
}

export function ChartCard({ title, description, className, children }: Readonly<ChartCardProps>) {
  return (
    <MotionSection>
      <Card className={cn("w-full overflow-hidden", className)}>
        <CardHeader className="flex-row items-start justify-between gap-4">
          <div>
            <CardTitle className="text-base">{title}</CardTitle>
            {description ? <CardDescription>{description}</CardDescription> : null}
          </div>
          <LivingIcon icon={Activity} label="تحلیل زنده" tone="blue" size={17} />
        </CardHeader>
        <CardContent className="px-2 pb-2">{children}</CardContent>
      </Card>
    </MotionSection>
  );
}
