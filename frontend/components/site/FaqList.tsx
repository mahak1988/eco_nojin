"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";

import { cn } from "@/lib/utils";

const FAQS: { q: string; a: string }[] = [
  {
    q: "اکو نوژین چیست؟",
    a: "پلتفرم دانش‌بنیان و رایگان برای کشاورزی اقلیم‌هوشمند: مشاوره علمی با استناد، آموزش، پایش مزرعه، ماشین‌حساب‌های تخصصی و مسیر آینده اقتصاد کربن.",
  },
  {
    q: "هزینه استفاده چقدر است؟",
    a: "در حال حاضر همه سرویس‌ها رایگان‌اند. برنامه درآمدی آینده شفاف اعلام می‌شود.",
  },
  {
    q: "پاسخ‌های مشاوره چقدر معتبرند؟",
    a: "پاسخ‌ها از دانشنامه علمی (FAO و همکاران) بازیابی می‌شوند و منبع هر پاسخ نمایش داده می‌شود؛ مدل هیچ محتوایی را از حافظه اختراع نمی‌کند.",
  },
  {
    q: "به چه زبان‌هایی پاسخ می‌دهید؟",
    a: "۱۴ زبان: فارسی، انگلیسی، عربی، اردو، روسی، چینی، هندی، بنگالی، اسپانیایی، فرانسوی، آلمانی، پرتغالی، ایتالیایی و مالایی.",
  },
  {
    q: "آیا به اینترنت پرسرعت نیاز است؟",
    a: "خیر؛ نسخه وب با PWA آفلاین کار می‌کند و ربات‌های تلگرام/ایتا روی اینترنت معمولی هم پاسخ می‌دهند.",
  },
  {
    q: "داده‌های من چگونه محافظت می‌شود؟",
    a: "رمزنگاری، سیاست‌های RLS در دیتابیس و ثبت رویدادها (audit log) فعال است؛ سیاست کامل در صفحه حریم خصوصی آمده است.",
  },
  {
    q: "داده ماهواره چه زمانی واقعی می‌شود؟",
    a: "در حال حاضر داده پایش شبیه‌سازی است و این صادقانه برچسب خورده (W-001). از فاز ۴ خط لوله کوپرنیکوس داده واقعی را جایگزین می‌کند.",
  },
  {
    q: "آیا توکن یا اعتبار کربن عرضه می‌شود؟",
    a: "خیر؛ با توجه به محدودیت‌های قانونی تبلیغ رمزارز در ایران، هر عرضه‌ای تنها پس از مشاوره حقوقی و اخذ مجوز انجام می‌شود.",
  },
];

export default function FaqList() {
  const [open, setOpen] = useState<number | null>(0);

  return (
    <div className="space-y-2">
      {FAQS.map((f, i) => (
        <div key={i} className="overflow-hidden rounded-xl border border-border">
          <button
            className="flex w-full items-center justify-between gap-3 px-4 py-3.5 text-right text-sm font-semibold text-foreground transition-colors hover:bg-muted/40"
            onClick={() => setOpen(open === i ? null : i)}
          >
            {f.q}
            <ChevronDown
              className={cn("h-4 w-4 shrink-0 text-muted-foreground transition-transform", open === i && "rotate-180")}
            />
          </button>
          {open === i && (
            <p className="border-t border-border px-4 py-3.5 text-sm leading-7 text-muted-foreground">{f.a}</p>
          )}
        </div>
      ))}
    </div>
  );
}
