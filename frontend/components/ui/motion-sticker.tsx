"use client";

import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface MotionStickerProps {
  readonly label: string;
  readonly icon?: LucideIcon;
  readonly tone?: "green" | "orange" | "blue" | "rose";
  readonly className?: string;
}

const toneClasses = {
  green: "border-emerald-500/25 bg-emerald-500/10 text-emerald-700",
  orange: "border-orange-500/25 bg-orange-500/10 text-orange-700",
  blue: "border-sky-500/25 bg-sky-500/10 text-sky-700",
  rose: "border-rose-500/25 bg-rose-500/10 text-rose-700",
};

export function MotionSticker({ label, icon: Icon, tone = "green", className }: MotionStickerProps) {
  return (
    <motion.span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold",
        toneClasses[tone],
        className
      )}
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -2, rotate: -1 }}
      transition={{ type: "spring", stiffness: 280, damping: 20 }}
    >
      {Icon ? <Icon aria-hidden="true" size={13} /> : null}
      {label}
    </motion.span>
  );
}
