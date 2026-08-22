"use client";

import { motion, type Variants } from "framer-motion";
import { Flame, Thermometer, CloudRain, Satellite, Droplets, Leaf } from "lucide-react";

export type MotionIconName = "flame" | "thermometer" | "rain" | "satellite" | "droplet" | "leaf";

const ICONS: Record<MotionIconName, React.ElementType> = {
  flame: Flame,
  thermometer: Thermometer,
  rain: CloudRain,
  satellite: Satellite,
  droplet: Droplets,
  leaf: Leaf,
};

const VARIANTS: Record<MotionIconName, Variants> = {
  flame: {
    hover: { scale: [1, 1.25, 1], rotate: [0, -6, 5, 0], transition: { duration: 0.45 } },
    load: { scale: [1, 1.18, 1], rotate: [0, 4, -3, 0], transition: { duration: 0.7 } },
  },
  thermometer: {
    hover: { y: [0, -4, 0], transition: { duration: 0.4 } },
    load: { y: [0, 3, 0], transition: { duration: 0.6 } },
  },
  rain: {
    hover: { y: [0, 4, 0], transition: { duration: 0.4 } },
    load: { y: [0, -3, 0], transition: { duration: 0.6 } },
  },
  satellite: {
    hover: { rotate: [0, 15, 0], transition: { duration: 0.5 } },
    load: { rotate: [0, -10, 8, 0], transition: { duration: 0.8 } },
  },
  droplet: {
    hover: { scale: [1, 1.2, 1], transition: { duration: 0.4 } },
    load: { scale: [1, 1.15, 1], transition: { duration: 0.6 } },
  },
  leaf: {
    hover: { rotate: [0, -8, 6, 0], transition: { duration: 0.45 } },
    load: { y: [0, -3, 0], transition: { duration: 0.6 } },
  },
};

interface MotionIconProps {
  name: MotionIconName;
  size?: number;
  color?: string;
  className?: string;
  /** پخش انیمیشن فقط هنگام هاور (پیش‌فرض) یا یک‌بار هنگام ورود به دید */
  playOn?: "hover" | "load" | "both";
  label?: string;
}

/**
 * MotionIcon — آیکون متحرک بدون حلقه (loop).
 * انیمیشن فقط یک‌بار هنگام هاور یا ورود به دید پخش می‌شود تا حواس کاربر را پرت نکند.
 * جایگزین ایموجی‌های ثابت در کارت‌های داشبورد.
 */
export function MotionIcon({ name, size = 16, color, className, playOn = "hover", label }: MotionIconProps) {
  const Icon = ICONS[name];
  const v = VARIANTS[name];
  const animate =
    playOn === "load" ? "load" : playOn === "both" ? undefined : undefined;
  const whileHover = playOn === "hover" || playOn === "both" ? "hover" : undefined;
  const whileInView = playOn === "load" || playOn === "both" ? "load" : undefined;
  return (
    <motion.span
      className={cn("inline-flex", className)}
      variants={v}
      initial={false}
      whileHover={whileHover}
      whileInView={whileInView}
      viewport={{ once: true, amount: 0.5 }}
      role={label ? "img" : undefined}
      aria-label={label}
    >
      <Icon size={size} color={color} />
    </motion.span>
  );
}

// local cn (avoid barrel cycle)
import { cn } from "@/lib/utils";
