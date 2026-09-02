import FarmSimulator3D from '@/components/simulator/FarmSimulator3D';

export const metadata = {
  title: 'شبیه‌ساز سه‌بعدی مزرعه | Eco Nojin',
  description: 'شبیه‌سازی تعاملی توپوگرافی، رطوبت خاک و آب زیرزمینی',
};

export default function SimulatorPage() {
  return (
    <main className="w-full h-screen bg-slate-950">
      <FarmSimulator3D />
    </main>
  );
}