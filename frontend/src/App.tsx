import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { HomePage } from "./pages/HomePage";

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-50 text-slate-900 font-sans" dir="rtl">
        {/* هدر سایت */}
        <header className="bg-white border-b border-slate-200 sticky top-0 z-50 shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center gap-2">
                <span className="text-2xl">🌱</span>
                <h1 className="text-xl font-bold text-emerald-700">اکو نوژین</h1>
              </div>
              <nav className="hidden md:flex gap-6">
                <Link to="/" className="text-slate-600 hover:text-emerald-600 font-medium transition-colors">
                  خانه
                </Link>
                <Link to="/dashboard" className="text-slate-600 hover:text-emerald-600 font-medium transition-colors">
                  داشبورد
                </Link>
              </nav>
            </div>
          </div>
        </header>

        {/* محتوای اصلی */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Routes>
            <Route path="/" element={<HomePage />} />
            {/* مسیرهای دیگر بعداً اضافه می‌شوند */}
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}