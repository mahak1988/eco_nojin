import React, { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, Map, Sprout, CloudSun, 
  Settings, Bell, Search, Menu, X, Leaf 
} from 'lucide-react';

const menuItems = [
  { id: 'dashboard', label: 'داشبورد کلی', icon: LayoutDashboard, path: '/hydroma' },
  { id: 'land', label: 'تحلیل زمین', icon: Map, path: '/hydroma/land' },
  { id: 'soil', label: 'سلامت خاک', icon: Sprout, path: '/hydroma/soil' },
  { id: 'climate', label: 'اقلیم و آب', icon: CloudSun, path: '/hydroma/climate' },
  { id: 'settings', label: 'تنظیمات', icon: Settings, path: '/hydroma/settings' },
];

export default function HydromaLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <div dir="rtl" className="flex h-screen bg-slate-50 font-sans text-slate-800">
      {/* Sidebar */}
      <aside 
        className={`fixed inset-y-0 right-0 z-50 w-64 bg-white border-l border-slate-200 shadow-sm transition-transform duration-300 ease-in-out md:relative md:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : 'translate-x-full md:translate-x-0 md:w-20'
        }`}
      >
        <div className="flex h-16 items-center justify-between px-4 border-b border-slate-100">
          <div className={`flex items-center gap-2 ${!sidebarOpen && 'md:justify-center md:w-full'}`}>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-600 text-white">
              <Leaf size={20} />
            </div>
            {sidebarOpen && <span className="text-xl font-bold text-emerald-800">هیدروما</span>}
          </div>
          <button onClick={() => setSidebarOpen(!sidebarOpen)} className="md:hidden text-slate-500">
            <X size={24} />
          </button>
        </div>

        <nav className="mt-6 px-3 space-y-1">
          {menuItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <button
                key={item.id}
                onClick={() => navigate(item.path)}
                className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                  isActive 
                    ? 'bg-emerald-50 text-emerald-700' 
                    : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                } ${!sidebarOpen && 'md:justify-center md:px-2'}`}
              >
                <item.icon size={20} className={isActive ? 'text-emerald-600' : 'text-slate-500'} />
                {sidebarOpen && <span>{item.label}</span>}
              </button>
            );
          })}
        </nav>
      </aside>

      {/* Main Content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top Header */}
        <header className="flex h-16 items-center justify-between bg-white px-6 border-b border-slate-200">
          <div className="flex items-center gap-4">
            <button onClick={() => setSidebarOpen(!sidebarOpen)} className="md:hidden text-slate-500">
              <Menu size={24} />
            </button>
            <div className="relative hidden md:block">
              <Search className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
              <input 
                type="text" 
                placeholder="جستجو در مزارع، گزارش‌ها..." 
                className="h-10 w-64 rounded-lg border border-slate-200 bg-slate-50 pr-10 pl-4 text-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
              />
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <button className="relative rounded-full p-2 text-slate-500 hover:bg-slate-100">
              <Bell size={20} />
              <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-red-500 ring-2 ring-white"></span>
            </button>
            <div className="flex items-center gap-3 border-r border-slate-200 pr-4">
              <div className="h-9 w-9 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-700 font-bold">
                م
              </div>
              <div className="hidden md:block">
                <p className="text-sm font-medium text-slate-900">مدیر مزرعه</p>
                <p className="text-xs text-slate-500">admin@hydroma.ir</p>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto bg-slate-50 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}