import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useBilingual } from '../../hooks/useBilingual';
import { createMarketplace } from '../../lib/marketplaceApi';
import Seo from '../../components/ui/Seo';
import PageHeader from '../../components/sections/PageHeader';
import Reveal from '../../components/ui/Reveal';
import { Store, MapPin, Check, AlertCircle, Loader2, Globe, Scale, Award, Handshake, ClipboardList } from 'lucide-react';

interface FormData {
  name: string;
  marketplace_type: string;
  description: string;
  address: string;
  postal_code: string;
  location: string;
  village_id: string;
  founder_ids: string;
  e_commerce_rules: boolean;
  buy_sell_rules: boolean;
  rules_document: string;
  contact_email: string;
  contact_phone: string;
}

interface FormErrors {
  name?: string;
  marketplace_type?: string;
  village_id?: string;
  e_commerce_rules?: string;
  buy_sell_rules?: string;
}

export default function CreateMarketplace() {
  const { fa, isFa } = useBilingual();
  const navigate = useNavigate();
  const [formData, setFormData] = useState<FormData>({
    name: '',
    marketplace_type: 'rural',
    description: '',
    address: '',
    postal_code: '',
    location: '',
    village_id: '',
    founder_ids: '',
    e_commerce_rules: false,
    buy_sell_rules: false,
    rules_document: '',
    contact_email: '',
    contact_phone: '',
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [submitStatus, setSubmitStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState<string>('');

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};
    if (!formData.name.trim()) {
      newErrors.name = fa('نام بازارچه الزامی است', 'Marketplace name is required');
    }
    if (!formData.marketplace_type) {
      newErrors.marketplace_type = fa('نوع بازارچه الزامی است', 'Marketplace type is required');
    }
    if (!formData.village_id.trim()) {
      newErrors.village_id = fa('کد روستا الزامی است', 'Village code is required');
    }
    if (!formData.e_commerce_rules) {
      newErrors.e_commerce_rules = fa('قوانین تجارت الکترونیک باید پذیرفته شود', 'E-commerce rules must be accepted');
    }
    if (!formData.buy_sell_rules) {
      newErrors.buy_sell_rules = fa('قوانین خرید و فروش باید پذیرفته شود', 'Buy/sell rules must be accepted');
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;
    setSubmitStatus('loading');
    setErrorMessage('');
    try {
      const founders = formData.founder_ids.split(',').map((f) => f.trim()).filter(Boolean);
      await createMarketplace({
        name: formData.name,
        marketplace_type: formData.marketplace_type,
        description: formData.description,
        address: formData.address,
        postal_code: formData.postal_code,
        location: formData.location,
        village_id: formData.village_id,
        founder_ids: founders,
        e_commerce_rules_accepted: formData.e_commerce_rules,
        buy_sell_rules_accepted: formData.buy_sell_rules,
        rules_document: formData.rules_document,
        contact_email: formData.contact_email,
        contact_phone: formData.contact_phone,
      });
      setSubmitStatus('success');
      setTimeout(() => {
        navigate('/marketplace/directory');
      }, 2000);
    } catch (err) {
      setSubmitStatus('error');
      setErrorMessage(err instanceof Error ? err.message : fa('خطایی رخ داد', 'An error occurred'));
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    const checked = (e.target as HTMLInputElement).checked;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
    if (errors[name as keyof FormErrors]) {
      setErrors(prev => ({ ...prev, [name]: undefined }));
    }
  };

  const requirements = [
    { icon: Scale, fa: fa('پذیرش قوانین', 'Accept Rules'), desc: fa('قوانین تجارت الکترونیک', 'E-commerce laws') },
    { icon: ClipboardList, fa: fa('آدرس کامل', 'Full Address'), desc: fa('کد پستی تایید', 'Verified postal code') },
    { icon: Award, fa: fa('احراز هویت', 'Identity Verification'), desc: fa('هویت کامل اعضا', 'Full member identity') },
    { icon: Handshake, fa: fa('مدیریت شورا', 'Council Management'), desc: fa('نظارت شورای منظر', 'Village council oversight') },
  ];

  return (
    <>
      <Seo title={fa('ایجاد بازارچه', 'Create Marketplace')} path="/marketplace/create" />
      <div className="min-h-screen bg-[var(--color-sand-50)]">
        <PageHeader
          kicker={fa('فرصت', 'Opportunity')}
          title={fa('ایجاد بازارچه', 'Create Marketplace')}
          lead={fa('یک بازارچه روستایی یا عشایری تأسیس کنید و به فروشندگان امکان فروشگاه بدهید.', 'Create a rural or tribal marketplace and empower sellers.')}
        />

        <main className="px-4 py-8 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-3xl">
            <form onSubmit={handleSubmit} className="space-y-6" noValidate>
              <div className="bg-[var(--color-leaf-50)]/60 rounded-2xl border border-[var(--color-leaf-200)]/60 p-6 sm:p-8 backdrop-blur-sm">
                <h2 className="text-xl font-semibold text-[var(--color-night-100)] mb-6 flex items-center gap-2">
                  <Store className="h-5 w-5 text-[var(--color-leaf-400)]" aria-hidden />
                  {fa('اطلاعات بازارچه', 'Marketplace Information')}
                </h2>

                <div className="space-y-5">
                  <div>
                    <label htmlFor="name" className="block text-sm font-medium text-[var(--color-night-100)] mb-2">
                      {fa('نام بازارچه', 'Marketplace Name')} <span className="text-red-500">*</span>
                    </label>
                    <div className="relative">
                      <Store className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-night-200)] w-5 h-5" aria-hidden />
                      <input
                        id="name"
                        name="name"
                        type="text"
                        value={formData.name}
                        onChange={handleChange}
                        className={`w-full pl-10 pr-4 py-3 border rounded-xl bg-white text-[var(--color-night-100)] placeholder-[var(--color-night-200)]/50 focus:outline-none focus:ring-2 focus:ring-[var(--color-gold-500)] transition-colors ${
                          errors.name ? 'border-red-500' : 'border-[var(--color-sand-300)]'
                        }`}
                        placeholder={fa('نام بازارچه (مثال: بازارچه روستای گلستان)', 'Marketplace name')}
                        dir={isFa ? 'rtl' : 'ltr'}
                      />
                    </div>
                    {errors.name && (
                      <p className="mt-1.5 flex items-center gap-1.5 text-sm text-red-500">
                        <AlertCircle className="w-4 h-4" aria-hidden />{errors.name}
                      </p>
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="marketplace_type" className="block text-sm font-medium text-[var(--color-night-100)] mb-2">
                        {fa('نوع بازارچه', 'Type')} <span className="text-red-500">*</span>
                      </label>
                      <select
                        id="marketplace_type"
                        name="marketplace_type"
                        value={formData.marketplace_type}
                        onChange={handleChange}
                        className="w-full pl-10 pr-4 py-3 border rounded-xl bg-white text-[var(--color-night-100)] focus:outline-none focus:ring-2 focus:ring-[var(--color-gold-500)] transition-colors appearance-none"
                      >
                        <option value="rural">{fa('روستایی', 'Rural')}</option>
                        <option value="tribal">{fa('عشایری', 'Tribal')}</option>
                      </select>
                      {errors.marketplace_type && (
                        <p className="mt-1.5 flex items-center gap-1.5 text-sm text-red-500">
                          <AlertCircle className="w-4 h-4" aria-hidden />{errors.marketplace_type}
                        </p>
                      )}
                    </div>
                    <div>
                      <label htmlFor="village_id" className="block text-sm font-medium text-[var(--color-night-100)] mb-2">
                        {fa('کد روستا', 'Village Code')} <span className="text-red-500">*</span>
                      </label>
                      <div className="relative">
                        <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-night-200)] w-5 h-5" aria-hidden />
                        <input
                          id="village_id"
                          name="village_id"
                          type="text"
                          value={formData.village_id}
                          onChange={handleChange}
                          className={`w-full pl-10 pr-4 py-3 border rounded-xl bg-white text-[var(--color-night-100)] placeholder-[var(--color-night-200)]/50 focus:outline-none focus:ring-2 focus:ring-[var(--color-gold-500)] transition-colors ${
                            errors.village_id ? 'border-red-500' : 'border-[var(--color-sand-300)]'
                          }`}
                          placeholder={fa('کد روستا', 'Village code')}
                          dir="ltr"
                        />
                      </div>
                      {errors.village_id && (
                        <p className="mt-1.5 flex items-center gap-1.5 text-sm text-red-500">
                          <AlertCircle className="w-4 h-4" aria-hidden />{errors.village_id}
                        </p>
                      )}
                    </div>
                  </div>

                  <div>
                    <label htmlFor="address" className="block text-sm font-medium text-[var(--color-night-100)] mb-2">
                      {fa('آدرس کامل', 'Full Address')}
                    </label>
                    <textarea
                      id="address"
                      name="address"
                      value={formData.address}
                      onChange={handleChange}
                      rows={2}
                      className="w-full px-4 py-3 border rounded-xl bg-white text-[var(--color-night-100)] placeholder-[var(--color-night-200)]/50 focus:outline-none focus:ring-2 focus:ring-[var(--color-gold-500)] transition-colors resize-none"
                      placeholder={fa('آدرس کامل بازارچه', 'Full address')}
                      dir={isFa ? 'rtl' : 'ltr'}
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="postal_code" className="block text-sm font-medium text-[var(--color-night-100)] mb-2">
                        {fa('کد پستی', 'Postal Code')}
                      </label>
                      <input
                        id="postal_code"
                        name="postal_code"
                        type="text"
                        value={formData.postal_code}
                        onChange={handleChange}
                        className="w-full px-4 py-3 border border-[var(--color-sand-300)] rounded-xl bg-white text-[var(--color-night-100)] placeholder-[var(--color-night-200)]/50 focus:outline-none focus:ring-2 focus:ring-[var(--color-gold-500)] transition-colors"
                        placeholder={fa('کد پستی', 'Postal code')}
                        dir="ltr"
                      />
                    </div>
                    <div>
                      <label htmlFor="location" className="block text-sm font-medium text-[var(--color-night-100)] mb-2">
                        {fa('موقعیت', 'Location')}
                      </label>
                      <input
                        id="location"
                        name="location"
                        type="text"
                        value={formData.location}
                        onChange={handleChange}
                        className="w-full px-4 py-3 border border-[var(--color-sand-300)] rounded-xl bg-white text-[var(--color-night-100)] placeholder-[var(--color-night-200)]/50 focus:outline-none focus:ring-2 focus:ring-[var(--color-gold-500)] transition-colors"
                        placeholder={fa('موقعیت جغرافیایی', 'Location')}
                        dir={isFa ? 'rtl' : 'ltr'}
                      />
                    </div>
                  </div>

                  <div>
                    <label htmlFor="founder_ids" className="block text-sm font-medium text-[var(--color-night-100)] mb-2">
                      {fa('شناسه‌های بنیان‌گذاران', 'Founder IDs')}
                    </label>
                    <input
                      id="founder_ids"
                      name="founder_ids"
                      type="text"
                      value={formData.founder_ids}
                      onChange={handleChange}
                      className="w-full px-4 py-3 border border-[var(--color-sand-300)] rounded-xl bg-white text-[var(--color-night-100)] placeholder-[var(--color-night-200)]/50 focus:outline-none focus:ring-2 focus:ring-[var(--color-gold-500)] transition-colors"
                      placeholder={fa('شناسه‌های کاربری جدا شده با کاما (مثال: user1, user2)', 'User IDs separated by comma')}
                      dir="ltr"
                    />
                  </div>

                  <div>
                    <label htmlFor="description" className="block text-sm font-medium text-[var(--color-night-100)] mb-2">
                      {fa('توضیحات بازارچه', 'Description')}
                    </label>
                    <textarea
                      id="description"
                      name="description"
                      value={formData.description}
                      onChange={handleChange}
                      rows={3}
                      className="w-full px-4 py-3 border border-[var(--color-sand-300)] rounded-xl bg-white text-[var(--color-night-100)] placeholder-[var(--color-night-200)]/50 focus:outline-none focus:ring-2 focus:ring-[var(--color-gold-500)] transition-colors resize-none"
                      placeholder={fa('توضیحات بازارچه', 'Marketplace description')}
                      dir={isFa ? 'rtl' : 'ltr'}
                    />
                  </div>

                  <div className="bg-[var(--color-leaf-50)]/50 rounded-xl p-4 space-y-3">
                    <h3 className="text-sm font-bold text-[var(--color-night-100)] flex items-center gap-2">
                      <Scale className="h-4 w-4" aria-hidden />
                      {fa('قوانین و شرایط', 'Rules & Conditions')}
                    </h3>
                    <label className="flex items-start gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        name="e_commerce_rules"
                        checked={formData.e_commerce_rules}
                        onChange={handleChange}
                        className="mt-0.5 h-4 w-4 accent-[var(--color-leaf-500)]"
                      />
                      <span className="text-sm text-[var(--color-night-200)]">
                        {fa('من قوانین تجارت الکترونیک بازارچه را می‌پذیرم', 'I accept the e-commerce marketplace rules')}
                      </span>
                    </label>
                    {errors.e_commerce_rules && (
                      <p className="flex items-center gap-1.5 text-sm text-red-500 ml-7">
                        <AlertCircle className="w-4 h-4" aria-hidden />{errors.e_commerce_rules}
                      </p>
                    )}
                    <label className="flex items-start gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        name="buy_sell_rules"
                        checked={formData.buy_sell_rules}
                        onChange={handleChange}
                        className="mt-0.5 h-4 w-4 accent-[var(--color-leaf-500)]"
                      />
                      <span className="text-sm text-[var(--color-night-200)]">
                        {fa('من قوانین خرید و فروش بازارچه را می‌پذیرم', 'I accept the buy/sell marketplace rules')}
                      </span>
                    </label>
                    {errors.buy_sell_rules && (
                      <p className="flex items-center gap-1.5 text-sm text-red-500 ml-7">
                        <AlertCircle className="w-4 h-4" aria-hidden />{errors.buy_sell_rules}
                      </p>
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="contact_email" className="block text-sm font-medium text-[var(--color-night-100)] mb-2">
                        <Globe className="inline h-4 w-4 ml-1" aria-hidden /> {fa('ایمیل تماس', 'Contact Email')}
                      </label>
                      <input
                        id="contact_email"
                        name="contact_email"
                        type="email"
                        value={formData.contact_email}
                        onChange={handleChange}
                        className="w-full px-4 py-3 border border-[var(--color-sand-300)] rounded-xl bg-white text-[var(--color-night-100)] placeholder-[var(--color-night-200)]/50 focus:outline-none focus:ring-2 focus:ring-[var(--color-gold-500)] transition-colors"
                        placeholder="info@example.com"
                      />
                    </div>
                    <div>
                      <label htmlFor="contact_phone" className="block text-sm font-medium text-[var(--color-night-100)] mb-2">
                        <Store className="inline h-4 w-4 ml-1" aria-hidden /> {fa('تماس فروشگاه', 'Shop Phone')}
                      </label>
                      <input
                        id="contact_phone"
                        name="contact_phone"
                        type="tel"
                        value={formData.contact_phone}
                        onChange={handleChange}
                        className="w-full px-4 py-3 border border-[var(--color-sand-300)] rounded-xl bg-white text-[var(--color-night-100)] placeholder-[var(--color-night-200)]/50 focus:outline-none focus:ring-2 focus:ring-[var(--color-gold-500)] transition-colors"
                        placeholder={fa('شماره تماس', 'Contact number')}
                        dir="ltr"
                      />
                    </div>
                  </div>
                </div>
              </div>

              {submitStatus === 'success' && (
                <Reveal className="flex items-center gap-3 p-4 bg-green-50 border border-green-200 rounded-xl text-green-800">
                  <Check className="w-6 h-6 flex-shrink-0" aria-hidden />
                  <p className="font-medium">{fa('بازارچه با موفقیت ثبت شد و در انتظار تأیید ادمین است.', 'Marketplace created successfully, pending admin approval.')}</p>
                </Reveal>
              )}

              {submitStatus === 'error' && (
                <Reveal className="flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-xl text-red-800">
                  <AlertCircle className="w-6 h-6 flex-shrink-0" aria-hidden />
                  <p className="font-medium">{errorMessage}</p>
                </Reveal>
              )}

              <button
                type="submit"
                disabled={submitStatus === 'loading'}
                className="w-full py-4 px-6 bg-[var(--color-gold-500)] hover:bg-[var(--color-gold-600)] disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold rounded-xl transition-colors flex items-center justify-center gap-2"
              >
                {submitStatus === 'loading' && <Loader2 className="w-5 h-5 animate-spin" aria-hidden />}
                {submitStatus === 'loading' ? fa('در حال ثبت...', 'Submitting...') : fa('ایجاد بازارچه', 'Create Marketplace')}
              </button>
            </form>

            <Reveal className="mt-12 space-y-4">
              <h3 className="text-lg font-semibold text-[var(--color-night-100)]">{fa('شرایط ایجاد بازارچه', 'Marketplace Requirements')}</h3>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {requirements.map((req, index) => (
                  <Reveal key={index} delay={index * 0.1} className="p-5 bg-white rounded-xl border border-[var(--color-sand-200)]">
                    <req.icon className="h-8 w-8 mx-auto mb-3 text-[var(--color-leaf-400)]" aria-hidden />
                    <p className="text-center font-bold text-[var(--color-night-100)]">{req.fa}</p>
                    <p className="text-center text-xs text-[var(--color-night-200)]/60 mt-1">{req.desc}</p>
                  </Reveal>
                ))}
              </div>
            </Reveal>
          </div>
        </main>
      </div>
    </>
  );
}