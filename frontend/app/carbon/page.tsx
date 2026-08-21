"use client";

/**
 * Carbon Dashboard Page
 * 
 * NEW page - displays carbon credits and MRV reports.
 * Integrates with engine/hydroma/blockchain via Python API.
 */
export default function CarbonPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-blue-800">
            🌍 داشبورد کربن
          </h1>
          <p className="mt-2 text-gray-600">
            مدیریت اعتبارات کربن و گزارش‌های MRV
          </p>
        </div>
      </header>
      
      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-800">
              اعتبارات صادر شده
            </h3>
            <p className="text-3xl font-bold text-green-600 mt-2">
              -
            </p>
            <p className="text-sm text-gray-500">tCO2e</p>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-800">
              پروژه‌های فعال
            </h3>
            <p className="text-3xl font-bold text-blue-600 mt-2">
              -
            </p>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-800">
              ارزش کل
            </h3>
            <p className="text-3xl font-bold text-purple-600 mt-2">
              -
            </p>
            <p className="text-sm text-gray-500">USD</p>
          </div>
        </div>
        
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-blue-800">
            ℹ️ این داشبورد به‌زودی با داده‌های واقعی از موتور MRV پر خواهد شد.
          </p>
        </div>
      </main>
    </div>
  );
}
