import React, { useRef, useEffect, useState } from 'react';
import { Play, Pause, RotateCcw, Wind, Trees } from 'lucide-react';
import { Button, Card } from '../ui';

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  life: number;
}

interface WindbreakObj {
  x: number;
  y: number;
  width: number;
  height: number;
  porosity: number; // 0-1
}

interface WindSimulation2DProps {
  width?: number;
  height?: number;
  windSpeed?: number; // m/s
  windbreaks?: WindbreakObj[];
  onErosionCalculated?: (erosion: number) => void;
}

/**
 * شبیه‌ساز دو‌بعدی باد و فرسایش با Particle System
 * اثر بادشکن به‌صورت real-time نمایش داده می‌شود
 */
export const WindSimulation2D: React.FC<WindSimulation2DProps> = ({
  width = 800,
  height = 400,
  windSpeed: initialWindSpeed = 12,
  windbreaks: initialWindbreaks = [],
  onErosionCalculated,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>(0);
  const particlesRef = useRef<Particle[]>([]);
  const [isPlaying, setIsPlaying] = useState(true);
  const [windSpeed, setWindSpeed] = useState(initialWindSpeed);
  const [showWindbreak, setShowWindbreak] = useState(true);
  const [erosionRate, setErosionRate] = useState(0);

  const windbreak: WindbreakObj = {
    x: width * 0.5,
    y: height * 0.3,
    width: 20,
    height: height * 0.5,
    porosity: 0.4,
  };

  // ایجاد ذرات جدید
  const createParticle = (): Particle => ({
    x: 0,
    y: Math.random() * height,
    vx: windSpeed * (0.8 + Math.random() * 0.4),
    vy: (Math.random() - 0.5) * 2,
    life: 1,
  });

  // بررسی برخورد با بادشکن
  const checkWindbreakCollision = (p: Particle): boolean => {
    if (!showWindbreak) return false;
    const wb = windbreak;
    if (
      p.x >= wb.x - wb.width / 2 &&
      p.x <= wb.x + wb.width / 2 &&
      p.y >= wb.y &&
      p.y <= wb.y + wb.height
    ) {
      // اثر porosity: برخی ذرات رد می‌شوند
      if (Math.random() < wb.porosity) {
        p.vx *= 0.3; // کاهش سرعت
        return false;
      }
      return true; // برخورد و حذف
    }
    return false;
  };

  // محاسبه منطقه محافظت‌شده (downwind protection zone)
  const isInProtectedZone = (p: Particle): boolean => {
    if (!showWindbreak) return false;
    const wb = windbreak;
    const protectedDistance = wb.height * 10;
    if (
      p.x > wb.x + wb.width / 2 &&
      p.x < wb.x + wb.width / 2 + protectedDistance &&
      p.y >= wb.y - wb.height * 0.5 &&
      p.y <= wb.y + wb.height * 1.5
    ) {
      return true;
    }
    return false;
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // مقداردهی اولیه ذرات
    if (particlesRef.current.length === 0) {
      for (let i = 0; i < 300; i++) {
        particlesRef.current.push({
          x: Math.random() * width,
          y: Math.random() * height,
          vx: windSpeed * (0.8 + Math.random() * 0.4),
          vy: (Math.random() - 0.5) * 2,
          life: 1,
        });
      }
    }

    let erodedParticles = 0;

    const animate = () => {
      ctx.fillStyle = 'rgba(135, 206, 235, 0.15)';
      ctx.fillRect(0, 0, width, height);

      // ترسیم زمین
      const gradient = ctx.createLinearGradient(0, height - 50, 0, height);
      gradient.addColorStop(0, '#8b7355');
      gradient.addColorStop(1, '#654321');
      ctx.fillStyle = gradient;
      ctx.fillRect(0, height - 50, width, 50);

      // ترسیم بادشکن
      if (showWindbreak) {
        const wb = windbreak;
        // درختان
        for (let i = 0; i < 5; i++) {
          const treeX = wb.x - wb.width / 2 + (i * wb.width) / 4;
          ctx.fillStyle = '#2d5016';
          ctx.beginPath();
          ctx.arc(treeX, wb.y + wb.height * 0.3, 15, 0, Math.PI * 2);
          ctx.fill();
          ctx.fillStyle = '#654321';
          ctx.fillRect(treeX - 2, wb.y + wb.height * 0.3, 4, wb.height * 0.7);
        }

        // منطقه محافظت‌شده (visual guide)
        ctx.fillStyle = 'rgba(34, 197, 94, 0.08)';
        ctx.fillRect(
          wb.x + wb.width / 2,
          wb.y - wb.height * 0.5,
          wb.height * 10,
          wb.height * 2
        );
      }

      // به‌روزرسانی و ترسیم ذرات
      let localErosion = 0;
      particlesRef.current = particlesRef.current.filter((p) => {
        // حرکت
        p.x += p.vx * 0.3;
        p.y += p.vy;
        p.life -= 0.003;

        // اثر منطقه محافظت‌شده (کاهش سرعت)
        if (isInProtectedZone(p)) {
          p.vx *= 0.95;
        }

        // برخورد با بادشکن
        if (checkWindbreakCollision(p)) {
          return false;
        }

        // برخورد با زمین = فرسایش
        if (p.y >= height - 50) {
          localErosion++;
          return false;
        }

        // حذف ذرات قدیمی یا خارج از صفحه
        if (p.life <= 0 || p.x > width) {
          return false;
        }

        // ترسیم
        const alpha = Math.min(1, p.vx / 15);
        ctx.strokeStyle = `rgba(255, 255, 255, ${alpha * 0.6})`;
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(p.x, p.y);
        ctx.lineTo(p.x - p.vx * 2, p.y - p.vy * 2);
        ctx.stroke();

        return true;
      });

      // ایجاد ذرات جدید
      while (particlesRef.current.length < 300) {
        particlesRef.current.push(createParticle());
      }

      erodedParticles = erodedParticles * 0.95 + localErosion * 0.05;
      setErosionRate(Math.round(erodedParticles));
      if (onErosionCalculated) {
        onErosionCalculated(erodedParticles);
      }

      if (isPlaying) {
        animationRef.current = requestAnimationFrame(animate);
      }
    };

    animate();

    return () => {
      cancelAnimationFrame(animationRef.current);
    };
  }, [isPlaying, windSpeed, showWindbreak]);

  const reset = () => {
    particlesRef.current = [];
    setErosionRate(0);
  };

  return (
    <Card title="شبیه‌ساز باد و فرسایش" icon={<Wind size={20} />}>
      {/* Controls */}
      <div
        style={{
          display: 'flex',
          gap: '1rem',
          marginBottom: '1rem',
          alignItems: 'center',
          flexWrap: 'wrap',
        }}
      >
        <Button
          variant={isPlaying ? 'secondary' : 'primary'}
          onClick={() => setIsPlaying(!isPlaying)}
          icon={isPlaying ? <Pause size={16} /> : <Play size={16} />}
        >
          {isPlaying ? 'توقف' : 'شروع'}
        </Button>

        <Button variant="ghost" onClick={reset} icon={<RotateCcw size={16} />}>
          ریست
        </Button>

        <Button
          variant={showWindbreak ? 'primary' : 'secondary'}
          onClick={() => setShowWindbreak(!showWindbreak)}
          icon={<Trees size={16} />}
        >
          {showWindbreak ? 'بادشکن فعال' : 'بدون بادشکن'}
        </Button>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flex: 1, minWidth: 200 }}>
          <label style={{ fontSize: '0.875rem', whiteSpace: 'nowrap' }}>
            سرعت باد: {windSpeed.toFixed(1)} m/s
          </label>
          <input
            type="range"
            min="2"
            max="25"
            step="0.5"
            value={windSpeed}
            onChange={(e) => setWindSpeed(parseFloat(e.target.value))}
            style={{ flex: 1 }}
          />
        </div>

        <div
          style={{
            padding: '0.5rem 1rem',
            background: erosionRate > 50 ? 'rgba(239, 68, 68, 0.1)' : 'rgba(16, 185, 129, 0.1)',
            borderRadius: 'var(--radius-lg)',
            fontSize: '0.875rem',
            fontWeight: 600,
            color: erosionRate > 50 ? 'var(--color-error)' : 'var(--color-success)',
          }}
        >
          فرسایش: {erosionRate} ذره/ثانیه
        </div>
      </div>

      {/* Canvas */}
      <div
        style={{
          borderRadius: 'var(--radius-lg)',
          overflow: 'hidden',
          border: '1px solid var(--color-border)',
        }}
      >
        <canvas
          ref={canvasRef}
          width={width}
          height={height}
          style={{
            width: '100%',
            height: 'auto',
            display: 'block',
            background: 'linear-gradient(to bottom, #87CEEB 0%, #B0E0E6 100%)',
          }}
        />
      </div>

      {/* Info Panel */}
      <div
        style={{
          marginTop: '1rem',
          padding: '1rem',
          background: 'var(--color-surface)',
          borderRadius: 'var(--radius-lg)',
          fontSize: '0.875rem',
          lineHeight: 1.8,
        }}
      >
        <strong>💡 اصول علمی:</strong>
        <ul style={{ margin: '0.5rem 0 0 0', paddingRight: '1.25rem' }}>
          <li>بادشکن با <strong>porosity ۴۰٪</strong> بهینه‌ترین عملکرد را دارد</li>
          <li>منطقه محافظت‌شده: <strong>۱۰ برابر ارتفاع</strong> در جهت باد</li>
          <li>کاهش فرسایش بادی تا <strong>۶۰-۸۰٪</strong> با بادشکن صحیح</li>
        </ul>
      </div>
    </Card>
  );
};
