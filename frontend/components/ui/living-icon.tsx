"use client";

import { motion, type MotionProps } from "framer-motion";
import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface LivingIconProps extends Omit<MotionProps, "children"> {
  icon: LucideIcon;
  label?: string;
  tone?: "green" | "orange" | "blue" | "rose";
  size?: number;
  className?: string;
}

const toneClasses = {
  green: "bg-emerald-500/12 text-emerald-600 ring-emerald-500/20",
  orange: "bg-orange-500/12 text-orange-600 ring-orange-500/20",
  blue: "bg-sky-500/12 text-sky-600 ring-sky-500/20",
  rose: "bg-rose-500/12 text-rose-600 ring-rose-500/20",
};

export function LivingIcon({
  icon: Icon,
  label,
  tone = "green",
  size = 20,
  className,
  ...motionProps
}: LivingIconProps) {
  return (
    <motion.span
      aria-label={label}
      role={label ? "img" : undefined}
      className={cn(
        "relative inline-flex h-10 w-10 items-center justify-center rounded-2xl ring-1",
        toneClasses[tone],
        className
      )}
      initial={{ scale: 0.9, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      whileHover={{ scale: 1.08, rotate: 3 }}
      transition={{ type: "spring", stiffness: 320, damping: 18 }}
      {...motionProps}
    >
      <motion.span
        aria-hidden="true"
        animate={{ y: [0, -2, 0], rotate: [0, -2, 0] }}
        transition={{ duration: 3.2, repeat: Infinity, ease: "easeInOut" }}
      >
        <Icon size={size} strokeWidth={1.8} />
      </motion.span>
      <motion.span
        aria-hidden="true"
        className="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full bg-current"
        animate={{ scale: [0.7, 1, 0.7], opacity: [0.35, 1, 0.35] }}
        transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
      />
    </motion.span>
  );
}
