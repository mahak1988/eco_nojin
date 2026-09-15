import { useEffect, useState } from 'react';
import { ChevronUp } from 'lucide-react';

/** Scroll progress indicator at top of page. */
export default function ScrollProgress() {
  const [progress, setProgress] = useState(0);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      const scrollTop = window.scrollY;
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      if (docHeight > 0) {
        setProgress((scrollTop / docHeight) * 100);
      }
      setVisible(scrollTop > 300);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <>
      {/* Progress bar */}
      <div
        className="fixed top-0 left-0 z-50 h-1 bg-[var(--color-leaf-500)] transition-[width] duration-150"
        style={{ width: `${progress}%` }}
        role="progressbar"
        aria-valuenow={Math.round(progress)}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label="Scroll progress"
      />

      {/* Back to top button */}
      {visible && (
        <button
          type="button"
          onClick={scrollToTop}
          className="fixed bottom-6 left-6 z-50 inline-flex h-11 w-11 items-center justify-center rounded-full bg-[var(--color-leaf-500)] text-[var(--color-night-950)] shadow-lg shadow-leaf-900/40 transition-all hover:scale-110"
          aria-label="Back to top"
        >
          <ChevronUp className="h-5 w-5" aria-hidden />
        </button>
      )}
    </>
  );
}
