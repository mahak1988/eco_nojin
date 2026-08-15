'use client';
import { useEffect, useState } from 'react';

export type Breakpoint = 'mobile' | 'tablet' | 'laptop' | 'desktop' | 'wide';

export interface Breakpoints {
  isMobile: boolean;   // < 640px
  isTablet: boolean;   // 640px - 1023px
  isLaptop: boolean;   // 1024px - 1279px
  isDesktop: boolean;  // 1280px - 1535px
  isWide: boolean;     // >= 1536px
  breakpoint: Breakpoint;
  width: number;
}

export function useBreakpoint(): Breakpoints {
  const [state, setState] = useState<Breakpoints>({
    isMobile: false,
    isTablet: false,
    isLaptop: false,
    isDesktop: true,
    isWide: false,
    breakpoint: 'desktop',
    width: 1280,
  });

  useEffect(() => {
    const update = () => {
      const w = window.innerWidth;
      let bp: Breakpoint;
      if (w < 640) bp = 'mobile';
      else if (w < 1024) bp = 'tablet';
      else if (w < 1280) bp = 'laptop';
      else if (w < 1536) bp = 'desktop';
      else bp = 'wide';

      setState({
        isMobile: bp === 'mobile',
        isTablet: bp === 'tablet',
        isLaptop: bp === 'laptop',
        isDesktop: bp === 'desktop',
        isWide: bp === 'wide',
        breakpoint: bp,
        width: w,
      });
    };

    update();
    window.addEventListener('resize', update);
    return () => window.removeEventListener('resize', update);
  }, []);

  return state;
}
