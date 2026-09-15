import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useBilingual } from '../../hooks/useBilingual';
import { fetchProduct, uploadProductImages } from '../../lib/marketplaceApi';
import { useMarketplace } from '../../context/MarketplaceContext';
import type { Product } from '../../lib/marketplaceTypes';
import Seo from '../../components/ui/Seo';
import PageHeader from '../../components/sections/PageHeader';
import Reveal from '../../components/ui/Reveal';
import { ShoppingCart, Loader2, Image, X, AlertCircle, Leaf, Droplets, Globe } from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';

export default function ProductPage() {
  const { id } = useParams<{ id: string }>();
  const { fa, formatNumber } = useBilingual();
  const { addToCart } = useMarketplace();
  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [previewImage, setPreviewImage] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    fetchProduct(id).then((p) => { setProduct(p); setLoading(false); }).catch(() => setLoading(false));
  }, [id]);

  if (loading) {
    return <div className="flex justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-leaf-400" /></div>;
  }

  if (!product) {
    return (
      <div className="text-center py-20">
        <p className="text-[var(--color-night-200)]/60">{fa('محصول یافت نشد', 'Product not found')}</p>
        <Link to="/marketplace" className="mt-4 inline-block text-[var(--color-leaf-400)]">{fa('بازگشت', 'Back')}</Link>
      </div>
    );
  }

  const handleAdd = async () => {
    setAdding(true);
    await addToCart([{ product_id: product.id, quantity: 1 }]);
    setAdding(false);
  };

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;
    setUploading(true);
    setUploadError(null);
    try {
      const result = await uploadProductImages(id!, files);
      setProduct((prev) => prev ? { ...prev, images: result.images } : null);
      setUploading(false);
    } catch (err: any) {
      setUploadError(err.message || 'خطا در آپلود');
      setUploading(false);
    }
  };

  const handleRemoveImage = () => {
    setPreviewImage(null);
  };

  // Carbon footprint data for chart
  const carbonData = [
    { name: fa('کربن', 'CO₂'), value: product.carbon_footprint_kg_co2, unit: 'kg CO₂', color: '#22c55e' },
    { name: fa('آب', 'Water'), value: product.water_footprint_liters / 1000, unit: 'kL', color: '#06b6d4' },
  ];

  return (
    <>
      <Seo title={product.name} path={`/marketplace/products/${product.id}`} />
      <PageHeader kicker="محصول" title={product.name} lead={product.description || ''} />
      <section className="px-4 py-10 sm:px-6">
        <div className="mx-auto grid max-w-6xl gap-8 lg:grid-cols-2">
          <div className="glass rounded-3xl p-8 flex items-center justify-center bg-gradient-to-br from-[var(--color-leaf-500)]/10 to-night-900">
            <span className="text-8xl">🌾</span>
          </div>
          <div className="flex flex-col gap-4">
            <div className="flex items-end justify-between">
              <span className="text-3xl font-extrabold text-[var(--color-leaf-400)]">{formatNumber(product.price)} IRR/kg</span>
              <span className="rounded-full bg-[var(--color-sand-500)]/10 px-3 py-1 text-xs font-bold text-[var(--color-sand-300)]">{fa('کیلوگرم', 'kg')}</span>
            </div>
            <p className="text-sm text-[var(--color-night-200)]/60">{fa('تولیدکننده:', 'Producer:')} {product.producer_name}</p>
            {product.organic_certified && (
              <span className="w-fit rounded-full bg-[var(--color-leaf-500)]/15 px-3 py-1 text-xs font-bold text-[var(--color-leaf-300)]">{fa('ارگانیک', 'Organic')}</span>
            )}
            <p className="text-sm text-[var(--color-night-200)]/60">
              {fa('موجودی:', 'Stock:')} {product.quantity_available > 0 ? fa(`${formatNumber(product.quantity_available)} kg موجود`, 'In stock') : fa('ناموجود', 'Out of stock')}
            </p>
            {product.images && product.images.length > 0 && (
              <div className="relative mt-2">
                {previewImage ? (
                  <div className="relative rounded-2xl overflow-hidden border border-[var(--color-night-700)]/30">
                    <img src={previewImage} alt="Upload preview" className="h-48 w-full object-cover" />
                    <button
                      type="button"
                      onClick={handleRemoveImage}
                      className="absolute left-3 top-3 inline-flex items-center gap-1.5 rounded-full bg-black/60 px-2.5 py-1 text-[10px] font-bold text-white transition hover:bg-black/80"
                    >
                      <X className="h-3 w-3" aria-hidden />
                      {fa('حذف', 'Remove')}
                    </button>
                  </div>
                ) : (
                  <div className="rounded-2xl overflow-hidden border border-[var(--color-night-700)]/30">
                    <img src={product.images[0]} alt={product.name} className="h-48 w-full object-cover" />
                  </div>
                )}
                <label className="mt-2 inline-flex cursor-pointer items-center gap-1.5 rounded-lg border border-[var(--color-leaf-500)]/30 bg-[var(--color-leaf-500)]/5 px-3 py-1.5 text-xs font-bold text-[var(--color-leaf-300)] transition hover:bg-[var(--color-leaf-500)]/10">
                  <Image className="h-3.5 w-3.5" aria-hidden />
                  {uploading ? fa('در حال آپلود...', 'Uploading...') : fa('تصویر محصول', 'Product Image')}
                  <input type="file" accept="image/*" multiple className="hidden" onChange={handleImageUpload} disabled={uploading} />
                </label>
                {uploadError && <p className="mt-2 flex items-center gap-1.5 text-sm text-red-400"><AlertCircle className="h-4 w-4" />{uploadError}</p>}
              </div>
            )}
            <div className="flex gap-2">
              <button
                type="button"
                onClick={handleAdd}
                disabled={adding || product.quantity_available <= 0}
                className="inline-flex items-center gap-2 rounded-xl bg-[var(--color-leaf-500)] px-6 py-3 text-sm font-extrabold text-[var(--color-night-950)] transition hover:bg-[var(--color-leaf-400)] disabled:opacity-50"
              >
                <ShoppingCart className="h-4 w-4" aria-hidden />
                {fa('افزودن به سبد', 'Add to Cart')}
              </button>
            </div>
          </div>
        </div>
        <div className="mx-auto mt-12 max-w-4xl">
          {/* Environmental Impact Section */}
          <Reveal>
            <div className="glass rounded-3xl p-6">
              <h3 className="mb-4 text-lg font-extrabold text-[var(--color-night-100)] flex items-center gap-2">
                <Globe className="h-5 w-5 text-[var(--color-leaf-400)]" aria-hidden />
                {fa('تأثیر زیست‌محیطی', 'Environmental Impact')}
              </h3>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="h-48">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={carbonData} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
                      <XAxis type="number" tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: 'var(--color-night-200)' }} />
                      <YAxis type="category" dataKey="name" tickLine={false} axisLine={false} tick={{ fontSize: 12, fontWeight: 600, fill: 'var(--color-night-100)' }} width={60} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: 'var(--color-night-900)',
                          border: '1px solid var(--color-night-700)',
                          borderRadius: '8px',
                        }}
                      />
                      <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                        <Cell fill="#22c55e" />
                        <Cell fill="#06b6d4" />
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <div className="space-y-3">
                  <div className="flex items-center gap-3 p-3 rounded-xl bg-[var(--color-leaf-500)]/10">
                    <div className="p-2 rounded-lg bg-[var(--color-leaf-500)]/20">
                      <Leaf className="h-5 w-5 text-[var(--color-leaf-400)]" aria-hidden />
                    </div>
                    <div>
                      <p className="text-xs text-[var(--color-night-200)]/60">{fa('پایه کربن', 'Carbon Footprint')}</p>
                      <p className="font-bold text-[var(--color-night-100)]">{formatNumber(product.carbon_footprint_kg_co2)} kg CO₂/کگ</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 p-3 rounded-xl bg-[var(--color-aqua-500)]/10">
                    <div className="p-2 rounded-lg bg-[var(--color-aqua-500)]/20">
                      <Droplets className="h-5 w-5 text-[var(--color-aqua-400)]" aria-hidden />
                    </div>
                    <div>
                      <p className="text-xs text-[var(--color-night-200)]/60">{fa('پایه آب', 'Water Footprint')}</p>
                      <p className="font-bold text-[var(--color-night-100)]">{formatNumber(product.water_footprint_liters)} L/کگ</p>
                    </div>
                  </div>
                  {product.organic_certified && (
                    <div className="flex items-center gap-3 p-3 rounded-xl bg-green-500/10">
                      <div className="p-2 rounded-lg bg-green-500/20">
                        <span className="text-xl" role="img" aria-label="organic">🌿</span>
                      </div>
                      <div>
                        <p className="text-xs text-[var(--color-night-200)]/60">{fa('گواهی ارگانیک', 'Organic Certified')}</p>
                        <p className="font-bold text-green-400">{fa('بله', 'Yes')}</p>
                      </div>
                    </div>
                  )}
                  {product.pgs_certified && (
                    <div className="flex items-center gap-3 p-3 rounded-xl bg-yellow-500/10">
                      <div className="p-2 rounded-lg bg-yellow-500/20">
                        <span className="text-xl font-bold text-yellow-500">PGS</span>
                      </div>
                      <div>
                        <p className="text-xs text-[var(--color-night-200)]/60">{fa('گواهی PGS', 'PGS Certified')}</p>
                        <p className="font-bold text-yellow-400">{fa('بله', 'Yes')}</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </Reveal>

          <Reveal delay={0.05}>
            <h3 className="mb-4 text-lg font-extrabold text-[var(--color-night-100)]">{fa('محصولات مرتبط', 'Related')}</h3>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="glass glass-hover rounded-3xl p-4 text-center">
                  <span className="text-4xl block mb-2">🌾</span>
                  <p className="text-xs font-bold text-[var(--color-night-100)]">{fa('محصول نمونه', 'Sample')} {i}</p>
                </div>
              ))}
            </div>
          </Reveal>
        </div>
      </section>
    </>
  );
}
