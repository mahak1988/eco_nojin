'use client';
import { useRef } from 'react';
import { Lottie as LottieComponent } from 'lottie-react';
const Lottie = LottieComponent as any;

// شما باید فایل‌های JSON آیکون‌ها را از LottieFiles دانلود کنید
// و در پوشه‌ی `public/animations/` ذخیره کنید.
const ICON_MAP: Record<string, any> = {
  // در اینجا فایل‌های JSON را ایمپورت کنید یا مسیر آن‌ها را بدهید
  // مثال: thermometer: require('@/public/animations/thermometer.json'),
  // flame: require('@/public/animations/flame.json'),
};

interface MotionIconProps {
  name: string; // نام آیکون (مثل 'thermometer', 'flame', 'rain')
  size?: number;
  color?: string; // تغییر رنگ آیکون (اگر پشتیبانی کند)
  className?: string;
}

export function MotionIcon({ name, size = 24, className = '', ...props }: MotionIconProps) {
  const lottieRef = useRef<any>(null);

  const handleMouseEnter = () => {
    if (lottieRef.current) {
      lottieRef.current.play();
    }
  };

  const handleMouseLeave = () => {
    if (lottieRef.current) {
      lottieRef.current.stop();
    }
  };

  // اگر فایل JSON پیدا نشد، یک placeholder برگردان
  if (!ICON_MAP[name]) {
    return <span className={`block ${className}`} style={{ width: size, height: size }} />;
  }

  return (
    <div
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      className={`inline-block ${className}`}
      style={{ width: size, height: size }}
    >
      <Lottie
        lottieRef={lottieRef}
        animationData={ICON_MAP[name]}
        loop={false}
        autoplay={false}
        style={{ width: '100%', height: '100%' }}
        {...props}
      />
    </div>
  );
}