import React from 'react';
import { LayoutDashboard, AlertCircle } from 'lucide-react';

export default function SimulatorPage() {
  return (
    <div className="min-h-screen bg-slate-50 p-8">
      <div className="max-w-4xl mx-auto bg-white rounded-xl shadow-sm border border-slate-200 p-8">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-3 bg-emerald-100 rounded-lg">
            <LayoutDashboard className="w-6 h-6 text-emerald-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-800">SimulatorPage</h1>
            <p className="text-sm text-slate-500">ماژول هیدروما (Hydroma)</p>
          </div>
        </div>
        
        <div className="flex items-start gap-3 p-4 bg-amber-50 border border-amber-200 rounded-lg text-amber-800">
          <AlertCircle className="w-5 h-5 mt-0.5 flex-shrink-0" />
          <div>
            <p className="font-semibold mb-1">این صفحه در حال توسعه است</p>
            <p className="text-sm text-amber-700">
              زیرساخت این ماژول آماده است و به زودی کامپوننت‌های تخصصی (نمودارها، جداول و شبیه‌سازها) به آن اضافه خواهد شد.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
