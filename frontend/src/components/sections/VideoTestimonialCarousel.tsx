import { useState } from 'react';

/** Video testimonial carousel. */
export default function VideoTestimonialCarousel({
  testimonials,
}: {
  testimonials?: { name: string; role: string; text: string; avatar: string }[];
}) {
  const data = testimonials || [
    { name: 'دکتر سارا مهرپور', role: 'مدیر علمی', text: 'دقت و سرعت بی‌سابقه در پایش مناطق روستایی.', avatar: '👩‍🔬' },
    { name: 'مهندس رضا کریمی', role: 'مدیر فنی', text: 'مدل‌سازی سه‌بعدی فوق‌العاده دقیق.', avatar: '👨‍💻' },
    { name: 'دکتر نیلوفر حسینی', role: 'محقق ارشد', text: 'توانمندسازی جامعه‌ها با ابزارهای دیجیتال.', avatar: '👩‍🌾' },
  ];
  const [current, setCurrent] = useState(0);

  return (
    <div className="space-y-4">
      <div className="rounded-3xl glass p-6 min-h-[160px]">
        <p className="text-sm text-[var(--color-night-100)]/80 leading-6">{data[current].text}</p>
        <div className="mt-4 flex items-center gap-3">
          <span className="text-2xl">{data[current].avatar}</span>
          <div>
            <p className="text-sm font-bold text-[var(--color-leaf-300)]">{data[current].name}</p>
            <p className="text-xs text-[var(--color-night-200)]/50">{data[current].role}</p>
          </div>
        </div>
      </div>
      <div className="flex gap-2 justify-center">
        {data.map((_, i) => (
          <button
            key={i}
            type="button"
            onClick={() => setCurrent(i)}
            className={`h-2 w-2 rounded-full transition-all ${i === current ? 'bg-[var(--color-leaf-500)] w-6' : 'bg-white/20'}`}
            aria-label={`Slide ${i + 1}`}
          />
        ))}
      </div>
    </div>
  );
}
