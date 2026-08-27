import React, { useEffect, useState } from 'react';
import { GraduationCap, ChevronDown, CheckCircle2, Circle } from 'lucide-react';

interface LessonMeta {
  id?: string;
  title?: string;
  minutes?: number;
}

interface CourseMeta {
  id?: string;
  title?: string;
  level?: string;
  duration_min?: number;
  description?: string;
  lesson_count?: number;
  lessons?: LessonMeta[];
}

interface LessonFull {
  id?: string;
  title?: string;
  minutes?: number;
  content?: string;
}

/**
 * فاز ۶-ج — LMS: دوره‌های آموزشی رایگان از بک‌اند (محتوا واقعی، فارسی).
 * پیشرفت درس‌ها در localStorage ذخیره می‌شود؛ اتصال به دیتابیس پس از ساخت جدول LMS.
 */
export const LmsCard: React.FC = () => {
  const [courses, setCourses] = useState<CourseMeta[]>([]);
  const [status, setStatus] = useState<'loading' | 'ok' | 'error'>('loading');
  const [openId, setOpenId] = useState<string | null>(null);
  const [lessons, setLessons] = useState<Record<string, LessonFull[]>>({});
  const [busyId, setBusyId] = useState<string | null>(null);
  const [progress, setProgress] = useState<Record<string, boolean>>(() => {
    try {
      return JSON.parse(localStorage.getItem('lms_progress') ?? '{}') as Record<string, boolean>;
    } catch {
      return {};
    }
  });

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const res = await fetch('/api/v1/lms/courses');
        const d = (await res.json()) as { status?: string; courses?: CourseMeta[]; error?: string };
        if (!alive) return;
        if (d.status === 'ok') {
          setCourses(d.courses ?? []);
          setStatus('ok');
        } else {
          setStatus('error');
        }
      } catch {
        if (alive) setStatus('error');
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  const toggle = async (id: string) => {
    if (openId === id) {
      setOpenId(null);
      return;
    }
    setOpenId(id);
    if (!lessons[id]) {
      setBusyId(id);
      try {
        const res = await fetch(`/api/v1/lms/courses/${id}`);
        const d = (await res.json()) as { status?: string; course?: { lessons?: LessonFull[] } };
        if (d.status === 'ok') setLessons((prev) => ({ ...prev, [id]: d.course?.lessons ?? [] }));
      } catch {
        /* ignore */
      } finally {
        setBusyId(null);
      }
    }
  };

  const mark = (lessonKey: string) => {
    const next = { ...progress, [lessonKey]: !progress[lessonKey] };
    setProgress(next);
    localStorage.setItem('lms_progress', JSON.stringify(next));
  };

  return (
    <div className="card" style={{ padding: '1.1rem', marginTop: '1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.7rem' }}>
        <h3 style={{ fontSize: '1.05rem', fontWeight: 800, margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#0d9488' }}>
          <GraduationCap size={17} /> یادگیری (LMS)
        </h3>
        {status === 'ok' && <span style={{ fontSize: '0.72rem', color: 'var(--color-text-secondary)' }}>{courses.length} دوره رایگان</span>}
      </div>

      {status === 'loading' && <p style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>در حال دریافت…</p>}
      {status === 'error' && <p style={{ fontSize: '0.82rem', color: '#ef4444' }}>⚠️ خطا در دریافت دوره‌ها</p>}

      {status === 'ok' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(230px, 1fr))', gap: '0.5rem' }}>
          {courses.map((c) => {
            const done = (c.lessons ?? []).filter((l) => progress[`${c.id}/${l.id}`]).length;
            const total = c.lesson_count ?? 0;
            return (
              <div key={c.id} style={{ border: '1px solid var(--color-border)', borderRadius: 12, background: 'var(--color-bg)', overflow: 'hidden' }}>
                <button onClick={() => void toggle(c.id ?? '')} style={{ width: '100%', textAlign: 'right', border: 'none', background: 'transparent', padding: '0.7rem 0.8rem', cursor: 'pointer' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '0.4rem' }}>
                    <span style={{ fontWeight: 800, fontSize: '0.86rem' }}>{c.title}</span>
                    <ChevronDown size={14} style={{ transform: openId === c.id ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }} />
                  </div>
                  <div style={{ fontSize: '0.68rem', color: 'var(--color-text-secondary)', marginTop: '0.15rem' }}>
                    {c.level} · {c.duration_min} دقیقه · {total} درس
                  </div>
                  {c.description && <div style={{ fontSize: '0.7rem', color: 'var(--color-text-secondary)', marginTop: '0.3rem' }}>{c.description}</div>}
                  <div style={{ height: 5, borderRadius: 4, background: 'var(--color-border)', marginTop: '0.5rem', overflow: 'hidden' }}>
                    <div style={{ width: `${total ? (done / total) * 100 : 0}%`, height: '100%', background: '#0d9488' }} />
                  </div>
                </button>
                {openId === c.id && (
                  <div style={{ borderTop: '1px solid var(--color-border)', padding: '0.5rem 0.8rem 0.7rem' }}>
                    {busyId === c.id && <p style={{ fontSize: '0.72rem', color: 'var(--color-text-secondary)' }}>در حال بارگذاری…</p>}
                    {(lessons[c.id ?? ''] ?? []).map((l) => {
                      const key = `${c.id}/${l.id}`;
                      const isDone = Boolean(progress[key]);
                      return (
                        <div key={key} style={{ display: 'flex', gap: '0.45rem', alignItems: 'flex-start', padding: '0.35rem 0', borderBottom: '1px dashed var(--color-border)' }}>
                          <button onClick={() => mark(key)} style={{ border: 'none', background: 'transparent', cursor: 'pointer', padding: 0, color: isDone ? '#10b981' : 'var(--color-text-secondary)', display: 'flex', marginTop: '0.1rem' }}>
                            {isDone ? <CheckCircle2 size={14} /> : <Circle size={14} />}
                          </button>
                          <div>
                            <div style={{ fontSize: '0.76rem', fontWeight: 700 }}>{l.title} <span style={{ fontWeight: 400, color: 'var(--color-text-secondary)' }}>({l.minutes} دقیقه)</span></div>
                            {isDone && l.content && <div style={{ fontSize: '0.7rem', color: 'var(--color-text-secondary)', marginTop: '0.2rem', lineHeight: 1.7 }}>{l.content}</div>}
                          </div>
                        </div>
                      );
                    })}
                    {total > 0 && (
                      <p style={{ fontSize: '0.68rem', color: 'var(--color-text-secondary)', margin: '0.45rem 0 0' }}>
                        پیشرفت: {done}/{total} درس — با تیک درس‌ها، محتوای کامل نمایش داده می‌شود.
                      </p>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {status === 'ok' && (
        <p style={{ fontSize: '0.7rem', color: 'var(--color-text-secondary)', margin: '0.6rem 0 0' }}>
          محتوای آموزشی واقعی و رایگان (منبع: بک‌اند اکو نوژین) — پیشرفت فعلاً محلی است؛ پس از ساخت جدول LMS در Supabase، ابری می‌شود.
        </p>
      )}
    </div>
  );
};
