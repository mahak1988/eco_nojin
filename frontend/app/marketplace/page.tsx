"use client";

/**
 * Marketplace Page
 * 
 * NEW page added to existing frontend.
 * Integrates with eco_nojin Python backend via API.
 */
export default function MarketplacePage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-green-50 to-white">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-green-800">
            🌱 بازارچه اکو نوژین
          </h1>
          <p className="mt-2 text-gray-600">
            محصولات ارگانیک و صنایع دستی روستایی
          </p>
        </div>
      </header>
      
      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-yellow-800">
            ⚠️ این صفحه در حال توسعه است. به زودی محصولات روستاهای همکار
            اضافه خواهد شد.
          </p>
        </div>
      </main>
    </div>
  );
}
