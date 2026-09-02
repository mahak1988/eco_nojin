'use client';

import { useState, useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Sky, Html, Environment, Stars } from '@react-three/drei';
import { motion } from 'framer-motion';
import { Droplets, Sun, Wind, Sprout } from 'lucide-react';

// استفاده از تایپ‌های تولید شده از بک‌اند (نمونه)
import type { components } from '@/lib/api/generated-schema';
type FarmData = components['schemas']['FarmOut'];

// کامپوننت زمین تعاملی
function InteractiveTerrain({ moisture }: { moisture: number }) {
  const meshRef = useRef<THREE.Mesh>(null);
  
  // تغییر رنگ زمین بر اساس رطوبت (از قهوه‌ای خشک به سبز سرسبز)
  const dryColor = [0.5, 0.35, 0.2]; // قهوه‌ای
  const wetColor = [0.2, 0.6, 0.3]; // سبز
  const r = dryColor[0] + (wetColor[0] - dryColor[0]) * (moisture / 100);
  const g = dryColor[1] + (wetColor[1] - dryColor[1]) * (moisture / 100);
  const b = dryColor[2] + (wetColor[2] - dryColor[2]) * (moisture / 100);

  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.1) * 0.05;
    }
  });

  return (
    <mesh ref={meshRef} rotation={[-Math.PI / 2, 0, 0]} position={[0, -1, 0]}>
      <planeGeometry args={[20, 20, 64, 64]} />
      <meshStandardMaterial 
        color={[r, g, b]} 
        roughness={0.8} 
        metalness={0.1}
      />
    </mesh>
  );
}

// کامپوننت سطح آب زیرزمینی
function Groundwater({ moisture }: { moisture: number }) {
  const yPosition = -0.8 + (moisture / 100) * 0.6;
  return (
    <mesh position={[0, yPosition, 0]} rotation={[-Math.PI / 2, 0, 0]}>
      <planeGeometry args={[20, 20]} />
      <meshPhysicalMaterial 
        color="#0ea5e9" 
        transparent 
        opacity={0.6} 
        roughness={0.1} 
        metalness={0.8}
        transmission={0.5}
      />
    </mesh>
  );
}

export default function FarmSimulator3D() {
  const [moisture, setMoisture] = useState(30);
  const [irrigation, setIrrigation] = useState(0);

  // شبیه‌سازی ساده تغییر رطوبت
  const handleIrrigationChange = (val: number) => {
    setIrrigation(val);
    setMoisture(Math.min(100, 30 + val * 0.7));
  };

  return (
    <div className="relative w-full h-screen bg-slate-950 text-white overflow-hidden">
      {/* --- بوم سه‌بعدی --- */}
      <Canvas camera={{ position: [5, 4, 5], fov: 50 }}>
        <Sky sunPosition={[100, 20, 100]} turbidity={0.5} rayleigh={0.5} />
        <ambientLight intensity={0.4} />
        <directionalLight position={[10, 10, 5]} intensity={1.5} castShadow />
        <Environment preset="sunset" />
        <Stars radius={100} depth={50} count={5000} factor={4} saturation={0} fade speed={1} />
        
        <InteractiveTerrain moisture={moisture} />
        <Groundwater moisture={moisture} />
        
        <OrbitControls 
          makeDefault 
          minPolarAngle={0} 
          maxPolarAngle={Math.PI / 2.2} 
          minDistance={3}
          maxDistance={15}
        />
      </Canvas>

      {/* --- رابط کاربری شناور (Glassmorphism) --- */}
      <motion.div 
        initial={{ x: 100, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ duration: 0.5 }}
        className="absolute top-6 right-6 w-80 bg-slate-900/60 backdrop-blur-xl border border-slate-700/50 rounded-2xl p-6 shadow-2xl"
      >
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-emerald-500/20 rounded-lg">
            <Sprout className="w-6 h-6 text-emerald-400" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white">شبیه‌ساز مزرعه</h2>
            <p className="text-xs text-slate-400">پلاک: NJ-0421 (نمونه)</p>
          </div>
        </div>

        {/* کارت‌های آمار */}
        <div className="grid grid-cols-2 gap-3 mb-6">
          <StatCard icon={<Droplets className="w-4 h-4 text-blue-400" />} label="رطوبت خاک" value={`${Math.round(moisture)}%`} />
          <StatCard icon={<Sun className="w-4 h-4 text-amber-400" />} label="تابش خورشید" value="850 W/m²" />
          <StatCard icon={<Wind className="w-4 h-4 text-slate-400" />} label="سرعت باد" value="12 km/h" />
          <StatCard icon={<Sprout className="w-4 h-4 text-emerald-400" />} label="سلامت محصول" value={moisture > 50 ? "عالی" : "تنش"} />
        </div>

        {/* کنترل‌ها */}
        <div className="space-y-4">
          <div>
            <div className="flex justify-between text-sm mb-2">
              <span className="text-slate-300">میزان آبیاری (میلی‌متر)</span>
              <span className="font-mono text-emerald-400">{irrigation} mm</span>
            </div>
            <input 
              type="range" 
              min="0" 
              max="100" 
              value={irrigation} 
              onChange={(e) => handleIrrigationChange(Number(e.target.value))}
              className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-emerald-500"
            />
          </div>
          
          <div className="pt-4 border-t border-slate-700/50">
            <p className="text-xs text-slate-400 leading-relaxed">
              💡 <span className="text-emerald-400 font-semibold">نکته علمی:</span> افزایش آبیاری باعث نفوذ به لایه‌های زیرین شده و سطح آب زیرزمینی را شبیه‌سازی می‌کند.
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
}

// کامپوننت کمکی برای کارت‌های آمار
function StatCard({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-3 flex flex-col items-center text-center">
      <div className="mb-2">{icon}</div>
      <span className="text-xs text-slate-400 mb-1">{label}</span>
      <span className="text-sm font-bold text-white">{value}</span>
    </div>
  );
}