/**
 * Phase 3 calculators — real, documented formulas (simplified field-level
 * estimates). Every result carries an honest note: these are educational
 * estimates, not engineering design.
 */

export interface CalcField {
  key: string;
  label: string;
  unit: string;
  placeholder: string;
  step?: number;
}

export interface CalcDef {
  id: string;
  title: string;
  formula: string;
  fields: CalcField[];
  compute: (v: Record<string, number>) => { result: string; note: string };
}

const fmt = (x: number): string =>
  Number.isFinite(x) ? x.toLocaleString("fa-IR", { maximumFractionDigits: 2 }) : "—";

export const CALCULATORS: Record<string, CalcDef> = {
  irrigation: {
    id: "irrigation",
    title: "نیاز آبیاری گیاه (FAO-56 ساده‌شده)",
    formula: "ETc = Kc × ETo  |  نیاز کل = ETc × مساحت × روز",
    fields: [
      { key: "kc", label: "ضریب گیاهی (Kc)", unit: "", placeholder: "مثلاً 1.1", step: 0.05 },
      { key: "eto", label: "تبخیر-تعرق مرجع (ETo)", unit: "mm/day", placeholder: "مثلاً 5", step: 0.1 },
      { key: "area", label: "مساحت", unit: "هکتار", placeholder: "مثلاً 1", step: 0.1 },
      { key: "days", label: "دوره آبیاری", unit: "روز", placeholder: "مثلاً 7", step: 1 },
    ],
    compute: (v) => {
      const etc = v.kc * v.eto;
      const totalM3 = (etc / 1000) * v.area * 10000 * v.days; // mm→m, ha→m²
      return {
        result: `نیاز روزانه ${fmt(etc)} میلی‌متر — حجم کل دوره: حدود ${fmt(totalM3)} مترمکعب`,
        note: "برآورد ساده‌شده بر پایه FAO-56؛ بارندگی مؤثر و راندمان آبیاری لحاظ نشده‌اند.",
      };
    },
  },
  "compost-cn": {
    id: "compost-cn",
    title: "ترکیب کمپوست برای نسبت C/N بهینه",
    formula: "C/N مخلوط ≈ (m1×C1 + m2×C2) / (m1×N1 + m2×N2)",
    fields: [
      { key: "straw", label: "وزن کاه", unit: "کیلوگرم", placeholder: "مثلاً 100", step: 5 },
      { key: "manure", label: "وزن کود دامی", unit: "کیلوگرم", placeholder: "مثلاً 50", step: 5 },
    ],
    compute: (v) => {
      // straw: C/N 80, manure: C/N 20 (typical)
      const cn = (v.straw * 80 + v.manure * 20) / (v.straw + v.manure);
      const ok = cn >= 25 && cn <= 35;
      return {
        result: `نسبت C/N مخلوط: حدود ${fmt(cn)}${ok ? " — در بازه بهینه ۲۵ تا ۳۵ ✓" : " — خارج از بازه بهینه (۲۵ تا ۳۵)"}`,
        note: "بر پایه مقادیر نمونه (کاه C/N≈80، کود دامی C/N≈20)؛ برای دقت بیشتر، آزمایش آزمایشگاهی بگیرید.",
      };
    },
  },
  fertilizer: {
    id: "fertilizer",
    title: "نیاز کود نیتروژنه",
    formula: "کود (kg) = (نیاز گیاه − نیتروژن خاک) × مساحت / (درصد N × راندمان)",
    fields: [
      { key: "target", label: "نیاز نیتروژن گیاه", unit: "kg/ha", placeholder: "مثلاً 120", step: 5 },
      { key: "soil_n", label: "نیتروژن موجود خاک", unit: "kg/ha", placeholder: "مثلاً 40", step: 5 },
      { key: "area", label: "مساحت", unit: "هکتار", placeholder: "مثلاً 1", step: 0.1 },
      { key: "pct", label: "درصد N کود (اوره=46)", unit: "%", placeholder: "46", step: 1 },
    ],
    compute: (v) => {
      const need = Math.max(0, v.target - v.soil_n) * v.area;
      const kg = need / ((v.pct / 100) * 0.6); // 60% efficiency
      return {
        result: `نیاز خالص: ${fmt(need)} کیلوگرم N — کود موردنیاز: حدود ${fmt(kg)} کیلوگرم`,
        note: "با راندمان ۶۰٪ برآورد شد؛ آزمون خاک و توصیه کارشناس جایگزین این برآورد آموزشی است.",
      };
    },
  },
  "carbon-stock": {
    id: "carbon-stock",
    title: "ذخیره کربن آلی خاک",
    formula: "SOC (t/ha) = C% × جرم مخصوص ظاهری × عمق × 10",
    fields: [
      { key: "c_pct", label: "کربن آلی خاک", unit: "%", placeholder: "مثلاً 1.5", step: 0.1 },
      { key: "bd", label: "جرم مخصوص ظاهری", unit: "g/cm³", placeholder: "مثلاً 1.3", step: 0.05 },
      { key: "depth", label: "عمق نمونه", unit: "سانتی‌متر", placeholder: "مثلاً 30", step: 5 },
      { key: "area", label: "مساحت", unit: "هکتار", placeholder: "مثلاً 1", step: 0.1 },
    ],
    compute: (v) => {
      const soc = v.c_pct * v.bd * (v.depth / 100) * 10; // t/ha
      const total = soc * v.area;
      const co2 = total * 3.67;
      return {
        result: `ذخیره کربن: ${fmt(soc)} تن در هکتار — کل: ${fmt(total)} تن C ≈ ${fmt(co2)} تن CO₂ معادل`,
        note: "بر پایه روش IPCC Tier 1؛ برای گزارش رسمی کربن، نمونه‌برداری استاندارد لازم است.",
      };
    },
  },
  erosion: {
    id: "erosion",
    title: "فرسایش خاک (RUSLE ساده‌شده)",
    formula: "A = R × K × LS × C × P  (تن در هکتار در سال)",
    fields: [
      { key: "r", label: "فرسایندگی باران (R)", unit: "", placeholder: "مثلاً 120", step: 5 },
      { key: "k", label: "فرسایش‌پذیری خاک (K)", unit: "", placeholder: "مثلاً 0.3", step: 0.01 },
      { key: "ls", label: "شیب و طول (LS)", unit: "", placeholder: "مثلاً 2", step: 0.1 },
      { key: "c", label: "پوشش گیاهی (C)", unit: "", placeholder: "مثلاً 0.2", step: 0.05 },
      { key: "p", label: "عملیات حفاظتی (P)", unit: "", placeholder: "مثلاً 0.8", step: 0.05 },
    ],
    compute: (v) => {
      const a = v.r * v.k * v.ls * v.c * v.p;
      return {
        result: `فرسایش برآوردی: ${fmt(a)} تن در هکتار در سال`,
        note: `${a > 10 ? "🚨 بالاتر از حد مجاز (~۱۰ تن) — اقدام حفاظتی توصیه می‌شود" : "در محدوده قابل قبول"} — RUSLE ساده‌شده؛ بررسی میدانی لازم است.`,
      };
    },
  },
  "water-footprint": {
    id: "water-footprint",
    title: "ردپای آب محصول",
    formula: "WF (m³/ton) = (ETc × 10) / عملکرد",
    fields: [
      { key: "etc", label: "نیاز آبی فصل (ETc)", unit: "mm", placeholder: "مثلاً 600", step: 10 },
      { key: "yield", label: "عملکرد", unit: "تن/هکتار", placeholder: "مثلاً 5", step: 0.1 },
    ],
    compute: (v) => {
      const wf = (v.etc * 10) / v.yield;
      return {
        result: `ردپای آب: ${fmt(wf)} مترمکعب به ازای هر تن محصول`,
        note: "ردپای آب سبز (باران) و خاکستری (آلودگی) لحاظ نشده — برآورد آبی صرف.",
      };
    },
  },
  seeding: {
    id: "seeding",
    title: "میزان بذر موردنیاز",
    formula: "بذر (kg/ha) = تراکم هدف / (جوانه‌زنی × بذر در کیلوگرم)",
    fields: [
      { key: "density", label: "تراکم هدف", unit: "بوته/ha", placeholder: "مثلاً 300000", step: 10000 },
      { key: "germ", label: "درصد جوانه‌زنی", unit: "%", placeholder: "مثلاً 90", step: 1 },
      { key: "seeds_kg", label: "تعداد بذر در کیلوگرم", unit: "دانه/kg", placeholder: "مثلاً 25000", step: 100 },
    ],
    compute: (v) => {
      const kg = v.density / ((v.germ / 100) * v.seeds_kg);
      return {
        result: `میزان بذر: حدود ${fmt(kg)} کیلوگرم در هکتار`,
        note: "خالص بذر زنده (PLS)؛ وزن هزار دانه و خلوص بذر باید از برچسب کیسه خوانده شود.",
      };
    },
  },
  lime: {
    id: "lime",
    title: "نیاز آهک برای اصلاح pH خاک",
    formula: "CaCO₃ (t/ha) ≈ (pH هدف − pH فعلی) × فاکتور بافت",
    fields: [
      { key: "ph_now", label: "pH فعلی", unit: "", placeholder: "مثلاً 5.2", step: 0.1 },
      { key: "ph_target", label: "pH هدف", unit: "", placeholder: "مثلاً 6.5", step: 0.1 },
      { key: "factor", label: "فاکتور بافت (لومی=1.5)", unit: "", placeholder: "1.5", step: 0.1 },
    ],
    compute: (v) => {
      const t = Math.max(0, v.ph_target - v.ph_now) * v.factor;
      return {
        result: `آهک خالص (CaCO₃): حدود ${fmt(t)} تن در هکتار`,
        note: "برآورد عمومی؛ نوع آهک (کشاورزی/آهک هیدراته) و عمق اختلاط نتیجه را تغییر می‌دهد.",
      };
    },
  },
  "soil-water": {
    id: "soil-water",
    title: "کمبود رطوبت خاک",
    formula: "کمبود (mm) = (رطوبت ظرفیت مزرعه − رطوبت فعلی) × عمق",
    fields: [
      { key: "fc", label: "رطوبت ظرفیت مزرعه", unit: "% حجمی", placeholder: "مثلاً 32", step: 0.5 },
      { key: "cur", label: "رطوبت فعلی", unit: "% حجمی", placeholder: "مثلاً 18", step: 0.5 },
      { key: "depth", label: "عمق ریشه", unit: "سانتی‌متر", placeholder: "مثلاً 40", step: 5 },
    ],
    compute: (v) => {
      const deficit = Math.max(0, v.fc - v.cur) * (v.depth / 10);
      return {
        result: `کمبود رطوبت: ${fmt(deficit)} میلی‌متر ≈ ${fmt(deficit / 10)} مترمکعب در هکتار`,
        note: "بر پایه رطوبت حجمی؛ با سنسور رطوبت یا روش وزنی اندازه‌گیری شود.",
      };
    },
  },
  "drip-design": {
    id: "drip-design",
    title: "طراحی ساده آبیاری قطره‌ای",
    formula: "تعداد قطره‌چکان = تراکم گیاه × مساحت | دبی کل = q × تعداد",
    fields: [
      { key: "density", label: "تراکم گیاه", unit: "بوته/ha", placeholder: "مثلاً 2500", step: 100 },
      { key: "area", label: "مساحت", unit: "هکتار", placeholder: "مثلاً 1", step: 0.1 },
      { key: "q", label: "دبی قطره‌چکان", unit: "لیتر/ساعت", placeholder: "مثلاً 4", step: 0.5 },
    ],
    compute: (v) => {
      const emitters = v.density * v.area;
      const flow = (emitters * v.q) / 1000; // m³/h
      return {
        result: `قطره‌چکان: حدود ${fmt(emitters)} عدد — دبی کل: ${fmt(flow)} مترمکعب در ساعت`,
        note: "بدون محاسبه افت فشار لوله‌ها؛ طراحی اجرایی نیاز به مهندس آبیاری دارد.",
      };
    },
  },
  biomass: {
    id: "biomass",
    title: "تخمین زیست‌توده خشک",
    formula: "زیست‌توده خشک = وزن تر × (1 − درصد رطوبت)",
    fields: [
      { key: "wet", label: "وزن تر نمونه", unit: "کیلوگرم", placeholder: "مثلاً 100", step: 1 },
      { key: "moist", label: "درصد رطوبت", unit: "%", placeholder: "مثلاً 65", step: 1 },
    ],
    compute: (v) => {
      const dry = v.wet * (1 - v.moist / 100);
      return {
        result: `زیست‌توده خشک: ${fmt(dry)} کیلوگرم`,
        note: "برآورد ساده؛ اندازه‌گیری رطوبت با آون استاندارد انجام می‌شود.",
      };
    },
  },
  "co2-offset": {
    id: "co2-offset",
    title: "معادل دی‌اکسیدکربن",
    formula: "CO₂ = کربن × 3.67 (نسبت جرم مولکولی)",
    fields: [
      { key: "c", label: "مقدار کربن", unit: "تن", placeholder: "مثلاً 10", step: 0.5 },
    ],
    compute: (v) => {
      const co2 = v.c * 3.67;
      return {
        result: `معادل ${fmt(co2)} تن CO₂`,
        note: "برای ادعای اعتبار کربن، به روش‌شناسی معتبر (مثل VM0042) و راستی‌آزمایی نیاز است.",
      };
    },
  },
};

export function getCalculator(id: string): CalcDef | undefined {
  return CALCULATORS[id];
}
