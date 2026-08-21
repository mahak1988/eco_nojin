"use client";

import { useState, useEffect, useRef } from "react";
import dynamic from "next/dynamic";
import { motion, useMotionValue, useTransform } from "framer-motion";
import {
  Leaf, Mountain, Droplet, TreePine, AlertTriangle,
  Cloud, MapPin, Sparkles, TrendingUp, Activity, Download,
  Wind, Sun, RefreshCw, DollarSign, Flame, Zap,
} from "lucide-react";

import { useI18n } from "@/lib/i18n-context";
import { useTheme } from "@/lib/theme-context";
import { API_BASE } from "@/lib/config";

// SSR-safe dynamic imports (same pattern as dashboard/page.tsx)
const CoordinatePicker = dynamic(
  () => import("@/components/maps/CoordinatePicker"),
  { ssr: false }
);

// ============================================================
// HOOK: Animated counter with easing
// ============================================================
function useAnimatedCounter(target: number, duration = 1200) {
  const [value, setValue] = useState(0);
  useEffect(() => {
    const start = performance.now();
    let raf = 0;
    const tick = (now: number) => {
      const p = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - p, 3); // easeOutCubic
      setValue(target * eased);
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, duration]);
  return value;
}

// ============================================================
// COMPONENT: 3D Tilt Card (exact copy of ModuleCard from dashboard)
// ============================================================
const MetricCard3D = ({
  title, icon: Icon, color, gradient, children, index = 0,
}: any) => {
  const { colors } = useTheme();
  const cardRef = useRef<HTMLDivElement>(null);
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const rotateX = useTransform(y, [-100, 100], [15, -15]);
  const rotateY = useTransform(x, [-100, 100], [-15, 15]);

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    x.set(e.clientX - rect.left - rect.width / 2);
    y.set(e.clientY - rect.top - rect.height / 2);
  };
  const handleMouseLeave = () => {
    x.set(0);
    y.set(0);
  };

  return (
    <motion.div
      ref={cardRef}
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ delay: index * 0.05 }}
      style={{
        rotateX, rotateY, transformStyle: "preserve-3d",
        padding: "20px", borderRadius: "20px",
        background: colors.cardBg,
        border: `1px solid ${colors.border}`,
        height: "100%",
      }}
      whileHover={{ y: -6, boxShadow: `0 20px 40px ${color}30` }}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      <div style={{
        width: 48, height: 48, borderRadius: 12,
        background: gradient,
        display: "flex", alignItems: "center", justifyContent: "center",
        marginBottom: 12,
        boxShadow: `0 8px 20px ${color}40`,
        transform: "translateZ(20px)",
      }}>
        <Icon size={24} color="white" />
      </div>
      <div style={{
        fontWeight: 700, color: colors.text,
        fontSize: "1rem", marginBottom: 12,
        transform: "translateZ(10px)",
      }}>
        {title}
      </div>
      <div style={{ transform: "translateZ(5px)" }}>{children}</div>
    </motion.div>
  );
};

// ============================================================
// COMPONENT: SVG Radar Chart (animated, theme-aware)
// ============================================================
function PlatformRadar({ data }: { data: { name: string; value: number; raw: string }[] }) {
  const { colors } = useTheme();
  const size = 340, center = size / 2, radius = 125;
  const n = data.length;
  const step = (2 * Math.PI) / n;
  const pt = (i: number, r: number) => ({
    x: center + r * Math.cos(i * step - Math.PI / 2),
    y: center + r * Math.sin(i * step - Math.PI / 2),
  });
  const poly = data.map((d, i) => `${pt(i, radius * d.value).x},${pt(i, radius * d.value).y}`).join(" ");

  return (
    <svg viewBox={`0 0 ${size} ${size}`} style={{ maxWidth: "100%", height: "auto" }}>
      <defs>
        <radialGradient id="radarFill">
          <stop offset="0%" stopColor={colors.primary} stopOpacity="0.6" />
          <stop offset="100%" stopColor={colors.accent} stopOpacity="0.15" />
        </radialGradient>
        <linearGradient id="radarStroke" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor={colors.primary} />
          <stop offset="100%" stopColor={colors.accent} />
        </linearGradient>
      </defs>
      {[0.25, 0.5, 0.75, 1].map((s, i) => (
        <motion.circle
          key={s} cx={center} cy={center} r={radius * s}
          fill="none" stroke={colors.border} strokeWidth="1"
          initial={{ scale: 0, opacity: 0 }}
          animate={{ scale: 1, opacity: 0.3 }}
          transition={{ delay: i * 0.1, duration: 0.4 }}
        />
      ))}
      {data.map((_, i) => {
        const p = pt(i, radius);
        return <line key={i} x1={center} y1={center} x2={p.x} y2={p.y}
          stroke={colors.border} strokeWidth="1" opacity="0.3" />;
      })}
      <motion.polygon
        points={poly}
        fill="url(#radarFill)" stroke="url(#radarStroke)" strokeWidth="2.5"
        initial={{ opacity: 0, scale: 0 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
      />
      {data.map((d, i) => {
        const p = pt(i, radius * d.value);
        return (
          <g key={i}>
            <motion.circle cx={p.x} cy={p.y} r="7"
              fill={colors.primary} stroke="white" strokeWidth="2.5"
              initial={{ scale: 0 }}
              animate={{ scale: [0, 1.3, 1] }}
              transition={{ delay: 0.3 + i * 0.1, duration: 0.5 }}
            />
            <motion.circle cx={p.x} cy={p.y} r="12"
              fill={colors.primary} opacity="0.3"
              animate={{ scale: [1, 1.8, 1], opacity: [0.5, 0, 0.5] }}
              transition={{ duration: 2, repeat: Infinity, delay: i * 0.2 }}
            />
          </g>
        );
      })}
      {data.map((d, i) => {
        const p = pt(i, radius + 32);
        return (
          <g key={i}>
            <text x={p.x} y={p.y - 6} textAnchor="middle"
              fill={colors.text} fontSize="12" fontWeight="700">
              {d.name}
            </text>
            <text x={p.x} y={p.y + 10} textAnchor="middle"
              fill={colors.primary} fontSize="11" fontWeight="700">
              {d.raw}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

// ============================================================
// COMPONENT: Animated NDVI Ring
// ============================================================
function NdviRing({ value, label }: { value: number; label: string }) {
  const { colors } = useTheme();
  const animated = useAnimatedCounter(value * 100, 1500);
  const color = value > 0.5 ? colors.success : value > 0.3 ? colors.warm : colors.danger;
  const circ = 2 * Math.PI * 45;
  return (
    <div style={{ position: "relative", width: 120, height: 120, margin: "0 auto" }}>
      <svg width="120" height="120" viewBox="0 0 120 120" style={{ transform: "rotate(-90deg)" }}>
        <circle cx="60" cy="60" r="45" fill="none" stroke={colors.border} strokeWidth="10" opacity="0.3" />
        <motion.circle
          cx="60" cy="60" r="45" fill="none" stroke={color} strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circ}
          initial={{ strokeDashoffset: circ }}
          animate={{ strokeDashoffset: circ - (circ * animated) / 100 }}
          transition={{ duration: 1.5, ease: [0.22, 1, 0.36, 1] }}
        />
      </svg>
      <div style={{
        position: "absolute", inset: 0,
        display: "flex", flexDirection: "column",
        alignItems: "center", justifyContent: "center",
      }}>
        <div style={{ fontSize: "1.6rem", fontWeight: 900, color: colors.text }}>
          {value.toFixed(2)}
        </div>
        <div style={{ fontSize: "0.7rem", color: colors.textMuted, fontWeight: 600 }}>
          {label}
        </div>
      </div>
    </div>
  );
}

// ============================================================
// HELPER: Risk color mapping
// ============================================================
const riskColor = (level: string, colors: any) => {
  const u = (level || "").toUpperCase();
  if (["LOW", "EXCELLENT", "GOOD"].includes(u)) return colors.success;
  if (["MEDIUM", "MODERATE"].includes(u)) return colors.warning;
  if (["HIGH", "CRITICAL", "POOR"].includes(u)) return colors.danger;
  return colors.textMuted;
};

// ============================================================
// MAIN COMPONENT
// ============================================================
export default function PlatformAnalysisPanel() {
  const { t, direction } = useI18n();
  const { colors } = useTheme();
  const reportRef = useRef<HTMLDivElement>(null);

  const [form, setForm] = useState({
    name: "", latitude: 35.6892, longitude: 51.389, area_ha: 50,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);

  // Animated KPI counters
  const carbonValue = useAnimatedCounter(result?.carbon?.annual_value_usd ?? 0, 1800);
  const totalCarbon = useAnimatedCounter(result?.carbon?.total_potential_tCO2e ?? 0, 1500);
  const ndviAnim = useAnimatedCounter(result?.vegetation?.avg_ndvi ?? 0, 1500);
  const erosionAnim = useAnimatedCounter(result?.erosion?.rusle_rate_t_ha_yr ?? 0, 1200);
  const et0Anim = useAnimatedCounter(result?.irrigation?.et0_mm_day ?? 0, 1200);
  const tempAnim = useAnimatedCounter(result?.climate?.temperature?.avg_mean_c ?? 0, 1200);

  const analyze = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/platform/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: form.name || "Web Analysis",
          latitude: form.latitude,
          longitude: form.longitude,
          area_ha: form.area_ha,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Analysis failed" }));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      setResult(await res.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const exportPng = async () => {
    if (!reportRef.current) return;
    try {
      const { default: html2canvas } = await import("html2canvas");
      const canvas = await html2canvas(reportRef.current, {
        backgroundColor: colors.bg, scale: 2, useCORS: true,
      });
      const a = document.createElement("a");
      a.download = `eco-nojin-${form.name || "analysis"}-${Date.now()}.png`;
      a.href = canvas.toDataURL("image/png");
      a.click();
    } catch (e: any) {
      setError(e.message);
    }
  };

  return (
    <div dir={direction} style={{ background: colors.bg, minHeight: "100vh" }}>
      <div style={{ maxWidth: 1500, margin: "0 auto", padding: "32px 20px" }}>

        {/* ============================================================
            HERO (same style as dashboard hero)
            ============================================================ */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          style={{
            background: `linear-gradient(135deg, ${colors.primary}, ${colors.accent})`,
            padding: 32, borderRadius: 24, color: "white",
            marginBottom: 32, position: "relative", overflow: "hidden",
          }}
        >
          {/* Animated floating orbs */}
          <motion.div
            animate={{ scale: [1, 1.2, 1], opacity: [0.2, 0.4, 0.2] }}
            transition={{ duration: 8, repeat: Infinity }}
            style={{
              position: "absolute", top: -80, right: -80,
              width: 250, height: 250, borderRadius: "50%",
              background: `radial-gradient(circle, rgba(255,255,255,0.3), transparent 70%)`,
              filter: "blur(30px)",
            }}
          />
          <motion.div
            animate={{ scale: [1, 1.3, 1], opacity: [0.2, 0.4, 0.2] }}
            transition={{ duration: 10, repeat: Infinity, delay: 2 }}
            style={{
              position: "absolute", bottom: -60, left: -60,
              width: 220, height: 220, borderRadius: "50%",
              background: `radial-gradient(circle, rgba(255,255,255,0.25), transparent 70%)`,
              filter: "blur(30px)",
            }}
          />

          <div style={{ display: "flex", alignItems: "center", gap: 16, position: "relative", zIndex: 1 }}>
            <motion.div
              animate={{ rotate: [0, 10, -10, 0] }}
              transition={{ duration: 4, repeat: Infinity }}
            >
              <Sparkles size={40} />
            </motion.div>
            <div style={{ flex: 1 }}>
              <h1 style={{ fontSize: "2rem", fontWeight: 800, margin: 0, lineHeight: 1.2 }}>
                {t("platform_title")}
              </h1>
              <p style={{ margin: "4px 0 0", opacity: 0.95, fontSize: "0.95rem" }}>
                {t("platform_subtitle")}
              </p>
            </div>
            <div style={{
              padding: "6px 14px", borderRadius: 20,
              background: "rgba(255,255,255,0.2)",
              backdropFilter: "blur(10px)",
              fontSize: "0.75rem", fontWeight: 700,
              letterSpacing: "0.5px",
            }}>
              {t("platform_badge")}
            </div>
          </div>
        </motion.div>

        {/* ============================================================
            INPUT FORM (3D card with CoordinatePicker)
            ============================================================ */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          style={{
            background: colors.cardBg, padding: 24, borderRadius: 20,
            border: `1px solid ${colors.border}`, marginBottom: 32,
          }}
        >
          <h2 style={{ color: colors.text, marginBottom: 20, fontSize: "1.5rem" }}>
            <MapPin size={24} style={{ display: "inline", verticalAlign: "middle", marginRight: 8 }} />
            {t("platform_location_input")}
          </h2>

          <CoordinatePicker
            lat={form.latitude}
            lon={form.longitude}
            onChange={(lat, lon) => setForm({ ...form, latitude: lat, longitude: lon })}
            height="320px"
          />

          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
            gap: 12, marginTop: 20,
          }}>
            <div>
              <label style={{ display: "block", fontSize: "0.85rem", fontWeight: 600, color: colors.textMuted, marginBottom: 6 }}>
                {t("platform_land_name")}
              </label>
              <input
                type="text"
                placeholder={t("platform_land_name_placeholder")}
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                style={{
                  width: "100%", padding: 12, borderRadius: 10,
                  border: `1px solid ${colors.border}`,
                  background: colors.bg, color: colors.text,
                  fontFamily: "inherit", fontSize: "0.95rem",
                  outline: "none", boxSizing: "border-box",
                }}
              />
            </div>
            <div>
              <label style={{ display: "block", fontSize: "0.85rem", fontWeight: 600, color: colors.textMuted, marginBottom: 6 }}>
                {t("platform_area_hectares")}
              </label>
              <input
                type="number" step="0.1" min="0.1"
                value={form.area_ha}
                onChange={(e) => setForm({ ...form, area_ha: parseFloat(e.target.value) || 0 })}
                style={{
                  width: "100%", padding: 12, borderRadius: 10,
                  border: `1px solid ${colors.border}`,
                  background: colors.bg, color: colors.text,
                  fontFamily: "inherit", fontSize: "0.95rem",
                  outline: "none", boxSizing: "border-box",
                }}
              />
            </div>
            <div style={{ display: "flex", alignItems: "flex-end" }}>
              <motion.button
                whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
                onClick={analyze}
                disabled={loading}
                style={{
                  width: "100%", padding: "14px 20px", borderRadius: 12,
                  background: loading
                    ? colors.textMuted
                    : `linear-gradient(135deg, ${colors.primary}, ${colors.accent})`,
                  color: "white", border: "none", cursor: loading ? "not-allowed" : "pointer",
                  fontWeight: 700, fontSize: "0.95rem", fontFamily: "inherit",
                  display: "flex", alignItems: "center", justifyContent: "center", gap: 8,
                  boxShadow: loading ? "none" : `0 8px 20px ${colors.primary}40`,
                }}
              >
                {loading ? (
                  <>
                    <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: "linear" }}>
                      <RefreshCw size={16} />
                    </motion.div>
                    {t("platform_analyzing")}
                  </>
                ) : (
                  <>
                    <Activity size={16} />
                    {t("platform_analyze_button")}
                  </>
                )}
              </motion.button>
            </div>
          </div>
        </motion.div>

        {/* ============================================================
            LOADING SKELETONS (dashboard style)
            ============================================================ */}
        {loading && (
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
              gap: 16, marginBottom: 32,
            }}
          >
            {[0, 1, 2, 3, 4, 5].map((i) => (
              <motion.div
                key={i}
                animate={{ y: [0, -4, 0] }}
                transition={{ duration: 2, repeat: Infinity, delay: i * 0.15 }}
                style={{
                  padding: 24, borderRadius: 20,
                  background: colors.cardBg,
                  border: `1px solid ${colors.border}`,
                  minHeight: 160,
                }}
              >
                <div style={{ display: "flex", gap: 12, marginBottom: 16 }}>
                  <motion.div
                    animate={{ opacity: [0.3, 0.7, 0.3] }}
                    transition={{ duration: 1.5, repeat: Infinity, delay: i * 0.1 }}
                    style={{ width: 48, height: 48, borderRadius: 12, background: colors.border }}
                  />
                  <div style={{ flex: 1 }}>
                    <motion.div animate={{ opacity: [0.3, 0.7, 0.3] }}
                      transition={{ duration: 1.5, repeat: Infinity }}
                      style={{ height: 14, background: colors.border, borderRadius: 8, width: "60%", marginBottom: 8 }} />
                    <motion.div animate={{ opacity: [0.3, 0.7, 0.3] }}
                      transition={{ duration: 1.5, repeat: Infinity, delay: 0.2 }}
                      style={{ height: 24, background: colors.border, borderRadius: 8, width: "80%" }} />
                  </div>
                </div>
                <motion.div animate={{ opacity: [0.3, 0.7, 0.3] }}
                  transition={{ duration: 1.5, repeat: Infinity, delay: 0.3 }}
                  style={{ height: 12, background: colors.border, borderRadius: 8, marginBottom: 6, width: "100%" }} />
                <motion.div animate={{ opacity: [0.3, 0.7, 0.3] }}
                  transition={{ duration: 1.5, repeat: Infinity, delay: 0.4 }}
                  style={{ height: 12, background: colors.border, borderRadius: 8, width: "70%" }} />
              </motion.div>
            ))}
          </motion.div>
        )}

        {/* ============================================================
            ERROR
            ============================================================ */}
        {error && !loading && (
          <motion.div
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            style={{
              padding: 24, borderRadius: 20, marginBottom: 32,
              background: colors.cardBg,
              border: `1px solid ${colors.danger}40`,
              borderInlineStart: `4px solid ${colors.danger}`,
              display: "flex", alignItems: "center", gap: 16,
            }}
          >
            <AlertTriangle color={colors.danger} size={28} />
            <div style={{ flex: 1 }}>
              <div style={{ color: colors.danger, fontWeight: 700, fontSize: "1rem" }}>
                {t("platform_error")}
              </div>
              <div style={{ color: colors.textMuted, fontSize: "0.85rem", marginTop: 4 }}>
                {error}
              </div>
            </div>
            <motion.button
              whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
              onClick={analyze}
              style={{
                padding: "10px 18px", borderRadius: 10,
                background: colors.danger, color: "white",
                border: "none", cursor: "pointer", fontWeight: 600,
                fontFamily: "inherit", fontSize: "0.85rem",
              }}
            >
              {t("platform_retry")}
            </motion.button>
          </motion.div>
        )}

        {/* ============================================================
            RESULTS
            ============================================================ */}
        {result && !loading && (
          <div ref={reportRef}>

            {/* ----- EXECUTIVE SUMMARY (hero KPI) ----- */}
            <motion.div
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.7 }}
              style={{
                padding: "40px 36px", borderRadius: 24,
                background: `linear-gradient(135deg, ${colors.primary}, ${colors.accent} 50%, ${colors.calm} 100%)`,
                color: "white", marginBottom: 32,
                position: "relative", overflow: "hidden",
                boxShadow: `0 20px 60px ${colors.primary}30`,
              }}
            >
              <motion.div
                animate={{ y: [0, -15, 0], rotate: [0, 180, 360] }}
                transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                style={{
                  position: "absolute", top: -30, right: -30,
                  width: 180, height: 180, borderRadius: "50%",
                  background: "rgba(255,255,255,0.08)",
                }}
              />
              <motion.div
                animate={{ y: [0, 15, 0], rotate: [0, -180, -360] }}
                transition={{ duration: 25, repeat: Infinity, ease: "linear" }}
                style={{
                  position: "absolute", bottom: -40, left: -40,
                  width: 160, height: 160, borderRadius: "50%",
                  background: "rgba(255,255,255,0.06)",
                }}
              />

              <div style={{ position: "relative", zIndex: 1, display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 24 }}>
                <div style={{ flex: 1, minWidth: 280 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10, opacity: 0.9, fontSize: "0.85rem" }}>
                    <MapPin size={14} />
                    <span>{result.location?.latitude?.toFixed(4)}°N, {result.location?.longitude?.toFixed(4)}°E</span>
                    <span style={{ opacity: 0.6 }}>•</span>
                    <span>{result.area_ha} ha</span>
                  </div>
                  <h2 style={{ fontSize: "clamp(1.8rem, 4vw, 2.5rem)", fontWeight: 900, margin: "0 0 8px 0", lineHeight: 1.1 }}>
                    {result.name || t("platform_unnamed")}
                  </h2>
                  <div style={{ opacity: 0.9, fontSize: "0.95rem" }}>
                    {result.climate?.koppen_description || result.climate?.koppen_class || "—"}
                  </div>
                </div>

                <div style={{ textAlign: "right" }}>
                  <div style={{ fontSize: "0.75rem", opacity: 0.85, marginBottom: 6, textTransform: "uppercase", letterSpacing: "1px", fontWeight: 600 }}>
                    {t("platform_annual_carbon_value")}
                  </div>
                  <div style={{ display: "flex", alignItems: "baseline", gap: 6, justifyContent: "flex-end" }}>
                    <DollarSign size={28} />
                    <span style={{ fontSize: "clamp(2.5rem, 6vw, 3.5rem)", fontWeight: 900, lineHeight: 1, letterSpacing: "-1px" }}>
                      {Math.round(carbonValue).toLocaleString()}
                    </span>
                  </div>
                  <div style={{ opacity: 0.85, fontSize: "0.85rem", marginTop: 6 }}>
                    {totalCarbon.toFixed(1)} tCO₂e · {t("platform_total_carbon")}
                  </div>
                </div>
              </div>
            </motion.div>

            {/* ----- 6 METRIC CARDS (3D Tilt) ----- */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              style={{ marginBottom: 32 }}
            >
              <h2 style={{ color: colors.text, marginBottom: 20, fontSize: "1.5rem" }}>
                {t("platform_metrics_title")}
              </h2>
              <div style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
                gap: 16,
              }}>
                {/* CLIMATE */}
                <MetricCard3D
                  title={t("platform_climate_title")}
                  icon={Cloud}
                  color={colors.accent}
                  gradient={`linear-gradient(135deg, ${colors.accent}, ${colors.accentDark})`}
                  index={0}
                >
                  <div style={{ fontSize: "1.6rem", fontWeight: 900, color: colors.text, marginBottom: 6 }}>
                    {tempAnim.toFixed(1)}°C
                  </div>
                  <div style={{ display: "flex", gap: 8, marginBottom: 10 }}>
                    <div style={{ flex: 1, padding: "8px 10px", background: `${colors.danger}15`, borderRadius: 8, fontSize: "0.8rem", display: "flex", alignItems: "center", gap: 4 }}>
                      <Sun size={12} color={colors.danger} />
                      {(result.climate?.temperature?.avg_max_c ?? 0).toFixed(1)}°
                    </div>
                    <div style={{ flex: 1, padding: "8px 10px", background: `${colors.accent}15`, borderRadius: 8, fontSize: "0.8rem", display: "flex", alignItems: "center", gap: 4 }}>
                      <Wind size={12} color={colors.accent} />
                      {(result.climate?.temperature?.avg_min_c ?? 0).toFixed(1)}°
                    </div>
                  </div>
                  <div style={{ padding: "8px 12px", background: `${colors.accent}10`, borderRadius: 8, fontSize: "0.85rem", color: colors.textMuted }}>
                    <Droplet size={13} style={{ display: "inline", marginRight: 6, verticalAlign: "middle" }} />
                    {(result.climate?.precipitation?.annual_mm ?? 0).toFixed(0)} mm/year
                  </div>
                </MetricCard3D>

                {/* VEGETATION */}
                <MetricCard3D
                  title={t("platform_vegetation_title")}
                  icon={Leaf}
                  color={colors.success}
                  gradient={`linear-gradient(135deg, ${colors.success}, #059669)`}
                  index={1}
                >
                  <NdviRing value={ndviAnim / 100 || result.vegetation?.avg_ndvi || 0} label="NDVI" />
                  <div style={{ textAlign: "center", marginTop: 10 }}>
                    <span style={{
                      padding: "6px 14px", borderRadius: 20,
                      background: `${riskColor(result.vegetation?.vegetation_health || result.vegetation?.health, colors)}20`,
                      color: riskColor(result.vegetation?.vegetation_health || result.vegetation?.health, colors),
                      display: "inline-block", fontSize: "0.8rem", fontWeight: 700,
                    }}>
                      {result.vegetation?.vegetation_health || result.vegetation?.health || "—"}
                    </span>
                  </div>
                </MetricCard3D>

                {/* EROSION */}
                <MetricCard3D
                  title={t("platform_erosion_title")}
                  icon={Mountain}
                  color={colors.warning}
                  gradient={`linear-gradient(135deg, ${colors.warning}, #d97706)`}
                  index={2}
                >
                  <div style={{ fontSize: "1.6rem", fontWeight: 900, color: colors.text, marginBottom: 4 }}>
                    {erosionAnim.toFixed(2)}
                    <span style={{ fontSize: "0.8rem", color: colors.textMuted, fontWeight: 500 }}> t/ha/yr</span>
                  </div>
                  <div style={{
                    padding: "6px 14px", borderRadius: 20,
                    background: `${riskColor(result.erosion?.risk_level, colors)}20`,
                    color: riskColor(result.erosion?.risk_level, colors),
                    display: "inline-block", fontSize: "0.8rem", fontWeight: 700, marginBottom: 10,
                  }}>
                    {result.erosion?.risk_level || "—"}
                  </div>
                  <div style={{ fontSize: "0.78rem", color: colors.textMuted }}>
                    R={(result.erosion?.r_factor ?? 0).toFixed(1)} · K={(result.erosion?.k_factor ?? 0).toFixed(2)} · LS={(result.erosion?.ls_factor ?? 0).toFixed(2)}
                  </div>
                </MetricCard3D>

                {/* IRRIGATION */}
                <MetricCard3D
                  title={t("platform_irrigation_title")}
                  icon={Droplet}
                  color={colors.cool}
                  gradient={`linear-gradient(135deg, ${colors.cool}, ${colors.accentDark})`}
                  index={3}
                >
                  <div style={{ fontSize: "1.6rem", fontWeight: 900, color: colors.text, marginBottom: 4 }}>
                    {et0Anim.toFixed(2)}
                    <span style={{ fontSize: "0.8rem", color: colors.textMuted, fontWeight: 500 }}> mm/day</span>
                  </div>
                  <div style={{ fontSize: "0.9rem", color: colors.textMuted, marginBottom: 10 }}>
                    {(result.irrigation?.annual_water_need_mm ?? 0).toFixed(0)} mm/year
                  </div>
                  <div style={{
                    padding: "6px 14px", borderRadius: 20,
                    background: `${colors.cool}20`, color: colors.cool,
                    display: "inline-block", fontSize: "0.8rem", fontWeight: 700, textTransform: "capitalize",
                  }}>
                    💧 {result.irrigation?.recommendation || result.irrigation?.irrigation_system || "—"}
                  </div>
                </MetricCard3D>

                {/* CARBON */}
                <MetricCard3D
                  title={t("platform_carbon_title")}
                  icon={TreePine}
                  color={colors.calm}
                  gradient={`linear-gradient(135deg, ${colors.calm}, #0f766e)`}
                  index={4}
                >
                  <div style={{ fontSize: "1.6rem", fontWeight: 900, color: colors.text, marginBottom: 4 }}>
                    {(result.carbon?.rate_tCO2e_ha_yr ?? 0).toFixed(2)}
                    <span style={{ fontSize: "0.8rem", color: colors.textMuted, fontWeight: 500 }}> tCO₂e/ha</span>
                  </div>
                  <div style={{
                    padding: "6px 14px", borderRadius: 20,
                    background: `${riskColor(result.carbon?.suitability, colors)}20`,
                    color: riskColor(result.carbon?.suitability, colors),
                    display: "inline-block", fontSize: "0.8rem", fontWeight: 700, marginBottom: 10,
                  }}>
                    🏆 {result.carbon?.suitability || "—"}
                  </div>
                  <div style={{ fontSize: "1.15rem", fontWeight: 800, color: colors.calm }}>
                    ${Math.round(result.carbon?.annual_value_usd || 0).toLocaleString()}/yr
                  </div>
                </MetricCard3D>

                {/* RISK */}
                <MetricCard3D
                  title={t("platform_risk_title")}
                  icon={AlertTriangle}
                  color={colors.danger}
                  gradient={`linear-gradient(135deg, ${colors.danger}, #b91c1c)`}
                  index={5}
                >
                  <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                    {Object.entries(result.risk_assessment || {})
                      .filter(([k, v]) => typeof v === "string" && !["insurance_recommendation", "overall_risk"].includes(k))
                      .slice(0, 4)
                      .map(([key, val]: any) => (
                        <div key={key} style={{
                          display: "flex", justifyContent: "space-between", alignItems: "center",
                          padding: "6px 10px", borderRadius: 8,
                          background: `${riskColor(val, colors)}10`,
                          fontSize: "0.78rem",
                        }}>
                          <span style={{ color: colors.textMuted, textTransform: "capitalize", fontWeight: 500 }}>
                            {key.replace(/_/g, " ")}
                          </span>
                          <span style={{
                            padding: "2px 10px", borderRadius: 12,
                            background: `${riskColor(val, colors)}25`, color: riskColor(val, colors),
                            fontWeight: 700, fontSize: "0.72rem",
                          }}>
                            {val}
                          </span>
                        </div>
                      ))}
                  </div>
                </MetricCard3D>
              </div>
            </motion.div>

            {/* ----- RADAR + RECOMMENDATIONS ----- */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              style={{ marginBottom: 32 }}
            >
              <h2 style={{ color: colors.text, marginBottom: 20, fontSize: "1.5rem" }}>
                {t("platform_deep_analysis")}
              </h2>
              <div style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))",
                gap: 16, alignItems: "start",
              }}>
                {/* RADAR */}
                <div style={{
                  padding: 24, borderRadius: 20,
                  background: colors.cardBg,
                  border: `1px solid ${colors.border}`,
                }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
                    <div style={{
                      width: 36, height: 36, borderRadius: 10,
                      background: `linear-gradient(135deg, ${colors.primary}, ${colors.accent})`,
                      display: "flex", alignItems: "center", justifyContent: "center",
                    }}>
                      <TrendingUp size={18} color="white" />
                    </div>
                    <h3 style={{ fontSize: "1rem", fontWeight: 700, color: colors.text, margin: 0 }}>
                      {t("platform_overview_chart")}
                    </h3>
                  </div>
                  <PlatformRadar
                    data={[
                      { name: t("platform_vegetation"), value: Math.max(0, Math.min(1, (result.vegetation?.avg_ndvi || 0) * 1.5)), raw: (result.vegetation?.avg_ndvi || 0).toFixed(2) },
                      { name: t("platform_carbon_title"), value: Math.min(1, (result.carbon?.rate_tCO2e_ha_yr || 0) / 3), raw: (result.carbon?.rate_tCO2e_ha_yr || 0).toFixed(2) },
                      { name: t("platform_soil_stability"), value: Math.max(0, 1 - (result.erosion?.rusle_rate_t_ha_yr || 0) / 50), raw: (result.erosion?.rusle_rate_t_ha_yr || 0).toFixed(2) },
                      { name: t("platform_rainfall"), value: Math.min(1, (result.climate?.precipitation?.annual_mm || 0) / 1000), raw: `${(result.climate?.precipitation?.annual_mm || 0).toFixed(0)}mm` },
                      { name: t("platform_drought_resistance"), value: ["HIGH","CRITICAL"].includes(String(result.risk_assessment?.drought || "").toUpperCase()) ? 0.2 : ["MEDIUM","MODERATE"].includes(String(result.risk_assessment?.drought || "").toUpperCase()) ? 0.5 : 0.9, raw: String(result.risk_assessment?.drought || "—") },
                    ]}
                  />
                </div>

                {/* RECOMMENDATIONS */}
                <div style={{
                  padding: 24, borderRadius: 20,
                  background: colors.cardBg,
                  border: `1px solid ${colors.border}`,
                }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
                    <div style={{
                      width: 36, height: 36, borderRadius: 10,
                      background: `linear-gradient(135deg, ${colors.warm}, ${colors.primary})`,
                      display: "flex", alignItems: "center", justifyContent: "center",
                    }}>
                      <Sparkles size={18} color="white" />
                    </div>
                    <h3 style={{ fontSize: "1rem", fontWeight: 700, color: colors.text, margin: 0 }}>
                      {t("platform_recommendations_title")}
                    </h3>
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                    {(result.recommendations || []).slice(0, 5).map((rec: any, idx: number) => {
                      const title = typeof rec === "string" ? rec : rec.title || "";
                      const priority = typeof rec === "object" ? rec.priority : "";
                      const priorityIcons: Record<string, string> = {
                        Critical: "🔴", High: "🟠", Medium: "🟡", Low: "🟢",
                      };
                      const icon = priorityIcons[priority] || "💡";
                      return (
                        <motion.div
                          key={idx}
                          initial={{ opacity: 0, x: 20 }}
                          whileInView={{ opacity: 1, x: 0 }}
                          viewport={{ once: true }}
                          transition={{ delay: idx * 0.08 }}
                          whileHover={{ x: 4 }}
                          style={{
                            display: "flex", alignItems: "flex-start", gap: 12,
                            padding: 14, borderRadius: 14,
                            background: `${colors.accent}08`,
                            border: `1px solid ${colors.border}`,
                            borderInlineStart: `3px solid ${colors.primary}`,
                            cursor: "default",
                          }}
                        >
                          <span style={{ fontSize: "1.2rem", flexShrink: 0 }}>{icon}</span>
                          <p style={{ margin: 0, fontSize: "0.88rem", lineHeight: 1.5, color: colors.text }}>
                            {title}
                          </p>
                        </motion.div>
                      );
                    })}
                    {(!result.recommendations || result.recommendations.length === 0) && (
                      <div style={{ padding: 24, textAlign: "center", color: colors.textMuted, fontSize: "0.9rem" }}>
                        {t("platform_no_recommendations")}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </motion.div>

            {/* ----- PERFORMANCE FOOTER ----- */}
            <motion.div
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              style={{
                padding: "16px 24px", borderRadius: 16,
                background: colors.cardBg,
                border: `1px solid ${colors.border}`,
                display: "flex", justifyContent: "space-between", alignItems: "center",
                flexWrap: "wrap", gap: 12, fontSize: "0.85rem",
              }}
            >
              <div style={{ display: "flex", gap: 20, flexWrap: "wrap", color: colors.textMuted }}>
                <span>⚡ <strong style={{ color: colors.text }}>{(result.performance?.total_ms || 0).toFixed(0)}ms</strong> {t("platform_processing_time")}</span>
                <span>🔧 C++: <strong style={{ color: colors.success }}>{result.performance?.cpp_calls || 0}</strong></span>
                <span>🌿 NDVI: <strong style={{ color: colors.accent }}>{(result.performance?.ndvi_ms || 0).toFixed(2)}ms</strong></span>
                <span>🏔️ RUSLE: <strong style={{ color: colors.warning }}>{(result.performance?.rusle_ms || 0).toFixed(2)}ms</strong></span>
              </div>
              <motion.button
                whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
                onClick={exportPng}
                style={{
                  padding: "8px 18px", borderRadius: 10,
                  background: `linear-gradient(135deg, ${colors.primary}, ${colors.accent})`,
                  color: "white", border: "none", cursor: "pointer",
                  fontWeight: 600, fontFamily: "inherit", fontSize: "0.85rem",
                  display: "flex", alignItems: "center", gap: 6,
                  boxShadow: `0 4px 12px ${colors.primary}30`,
                }}
              >
                <Download size={14} />
                {t("platform_export_png")}
              </motion.button>
            </motion.div>
          </div>
        )}
      </div>
    </div>
  );
}
