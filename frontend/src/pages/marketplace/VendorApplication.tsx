import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useBilingual } from '../../hooks/useBilingual';
import { applyVendor } from '../../lib/marketplaceApi';
import Seo from '../../components/ui/Seo';
import PageHeader from '../../components/sections/PageHeader';
import Reveal from '../../components/ui/Reveal';
import { FileText, MapPin, Store, UserPlus, Check, AlertCircle, Loader2, Truck, Award, ClipboardList, Package, DollarSign, Phone, Globe, Clock, Navigation } from 'lucide-react';

interface FormData {
  shop_name: string;
  description: string;
  location: string;
  village_id: string;
  product_types: string;
  certifications: string;
  production_capacity: string;
  years_experience: string;
  contact_phone: string;
  social_media: string;
  operating_hours: string;
  delivery_area: string;
  currency: string;
  marketplace_id: string;
}

interface FormErrors {
  shop_name?: string;
  description?: string;
  location?: string;
  village_id?: string;
  product_types?: string;
  certifications?: string;
  production_capacity?: string;
  years_experience?: string;
  contact_phone?: string;
  social_media?: string;
  operating_hours?: string;
  delivery_area?: string;
  currency?: string;
  marketplace_id?: string;
}

export default function VendorApplication() {
  const { fa, isFa } = useBilingual();
  const [formData, setFormData] = useState<FormData>({
    shop_name: '',
    description: '',
    location: '',
    village_id: '',
    product_types: '',
    certifications: '',
    production_capacity: '',
    years_experience: '',
    contact_phone: '',
    social_media: '',
    operating_hours: '',
    delivery_area: '',
    currency: 'IRR',
    marketplace_id: '',
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [submitStatus, setSubmitStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState<string>('');

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};
    if (!formData.shop_name.trim()) {
      newErrors.shop_name = fa('نام فروشگاه الزامی است', 'Shop name is required');
    }
    if (!formData.description.trim()) {
      newErrors.description = fa('توضیحات فروشگاه الزامی است', 'Shop description is required');
    } else if (formData.description.trim().length < 10) {
      newErrors.description = fa('توضیحات باید حداقل ۱۰ کاراکتر باشد', 'Description must be at least 10 characters');
    }
    if (!formData.location.trim()) {
      newErrors.location = fa('موقعیت الزامی است', 'Location is required');
    }
    if (!formData.village_id.trim()) {
      newErrors.village_id = fa('کد روستا الزامی است', 'Village code is required');
    }
    if (!formData.product_types.trim()) {
      newErrors.product_types = fa('نوع محصولات الزامی است', 'Product types are required');
    }
    if (!formData.certifications.trim()) {
      newErrors.certifications = fa('گواهینامه‌ها الزامی است', 'Certifications are required');
    }
    if (!formData.production_capacity.trim()) {
      newErrors.production_capacity = fa('ظرفیت تولید الزامی است', 'Production capacity is required');
    }
    if (!formData.years_experience.trim()) {
      newErrors.years_experience = fa('سال‌های تجربه الزامی است', 'Years of experience is required');
    }
    if (!formData.contact_phone.trim()) {
      newErrors.contact_phone = fa('شماره تماس الزامی است', 'Contact phone is required');
    }
    if (!formData.social_media.trim()) {
      newErrors.social_media = fa('لینک شبکه‌های اجتماعی الزامی است', 'Social media links are required');
    }
    if (!formData.operating_hours.trim()) {
      newErrors.operating_hours = fa('ساعات کاری الزامی است', 'Operating hours are required');
    }
    if (!formData.delivery_area.trim()) {
      newErrors.delivery_area = fa('حوزه تحویل الزامی است', 'Delivery area is required');
    }
    if (!formData.currency.trim()) {
      newErrors.currency = fa('ارز الزامی است', 'Currency is required');
    }
    if (!formData.marketplace_id.trim()) {
      newErrors.marketplace_id = fa('بازارچه الزامی است', 'Marketplace is required');
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
      await applyVendor(formData);
      setSubmitStatus('success');
      setFormData({ shop_name: '', description: '', location: '', village_id: '', product_types: '', certifications: '', production_capacity: '', years_experience: '', contact_phone: '', social_media: '', operating_hours: '', delivery_area: '', currency: 'IRR', marketplace_id: '' });
    } catch (err) {
      setSubmitStatus('error');
      setErrorMessage(err instanceof Error ? err.message : fa('خطایی رخ داد. لطفاً دوباره تلاش کنید', 'An error occurred. Please try again'));
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (errors[name as keyof FormErrors]) {
      setErrors(prev => ({ ...prev, [name]: undefined }));
    }
  };

  const requirements = [
    fa('دارای مشخصات کامل کسب‌وکار', 'Complete business information required'),
    fa('تأیید هویت', 'Identity verification'),
    fa('رعایت ضوابط کیفیت محصول', 'Product quality standards compliance'),
    fa('مشخصات نوع محصولات', 'Product type specifications'),
    fa('گواهینامه‌های معتبر', 'Valid certifications'),
    fa('شماره تماس و شبکه‌های اجتماعی', 'Contact & social media'),
  ];

  return (
    <>
      <Seo title="فروشنده شوید" path="/marketplace/apply" />
      <div className="min-h-screen bg-[var(--color-leaf-50)]/60">
        <PageHeader
          kicker={fa('فرصت', 'Opportunity')}
          title={fa('فروشنده شوید', 'Become a Vendor')}
          lead={fa('ثبت‌نام فروشگاه خود را در بازارگاه محلی اکو نوژین انجام دهید.', 'Register your shop in the Eco Nojin local marketplace.')}
        />

        <main className="px-4 py-8 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-3xl">
            <form onSubmit={handleSubmit} className="space-y-6" noValidate>
              <div className="bg-[var(--color-leaf-50)]/60 rounded-2xl border border-[var(--color-leaf-200)]/60 p-6 sm:p-8 backdrop-blur-sm">
                <h2 className="text-xl font-semibold text-[var(--color-night-100)] mb-6">
                  {fa('اطلاعات فروشگاه', 'Shop Information')}
                </h2>

                <div className="space-y-5">
                  <div>
                    <label htmlFor="shop_name" className="block text-sm font-medium text-[var(--color-night-100)] mb-2">
                      {fa('نام فروشگاه', 'Shop Name')} <span className="text-red-500">*</span>
                    </label>
                    <div className="relative">
                      <Store className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-night-200)] w-5 h-5" aria-hidden />
                      <input
                        id="shop_name"
                        name="shop_name"
                        type="text"
                        value={formData.shop_name}
                        onChange={handleChange}
                        className={`w-full pl-10 pr-4 py-3 border rounded-xl bg-white text-[var(--color-night-100)] placeholder-[var(--color-night-200)]/50 focus:outline-none focus:ring-2 focus:ring-[var(--color-gold-500)] transition-colors ${
                          errors.shop_name ? 'border-red-500' : 'border-[var(--color-sand-300)]'
                        }`}
                        placeholder={fa('مثال: ارگانیک گلستان', 'e.g., Golestan Organic')}
                        dir={isFa ? 'rtl' : 'ltr'}
                      />
                    </div>
                    {errors.shop_name && (
                      <p className="mt-1.5 flex items-center gap-1.5 text-sm text-red-500">
                        <AlertCircle className="w-4 h-4" aria-hidden />
                        {errors.shop_name}
                      </p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="description" className="block text-sm font-medium text-[var(--color-night-100)] mb-2">
                      {fa('توضیحات فروشگاه', 'Shop Description')} <span className="text-red-500">*</span>
                    </label>
                    <div className="relative">
                      <FileText className="absolute left-3 top-3 text-[var(--color-night-200)] w-5 h-5" aria-hidden />
                      <textarea
                        id="description"
                        name="description"
                        value={formData.description}
                        onChange={handleChange}
                        rows={5}
                        className={`w-full pl-10 pr-4 py-3 border rounded-xl bg-white text-[var(--color-night-100)] placeholder-[var(--color-night-200)]/50 focus:outline-none focus:ring-2 focus:ring-[var(--color-gold-500)] transition-colors resize-none ${
                          errors.description ? 'border-red-500' : 'border-[var(--color-sand-300)]'
                        }`}
                        placeholder={fa('درباره فروشگاه، محصولات و روش‌های تولید خود بنویسید (حداقل ۱۰ کاراکتر)', 'Describe your shop, products, and production methods (minimum 10 characters)')}
                        dir={isFa ? 'rtl' : 'ltr'}
                      />
                    </div>
                    {errors.description && (
                      <p className="mt-1.5 flex items-center gap-1.5 text-sm text-red-500">
                        <AlertCircle className="w-4 h-4" aria-hidden />
                        {errors.description}
                      </p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="location" className="block text-sm font-medium text-[var(--color-night-100)] mb-2">
                      {fa('موقعیت', 'Location')} <span className="text-red-500">*</span>
                    </label>
                    <div className="relative">
                      <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-night-200)] w-5 h-5" aria-hidden />
                      <input
                        id="location"
                        name="location"
                        type="text"
                        value={formData.location}
                        onChange={handleChange}
                        className={`w-full pl-10 pr-4 py-3 border rounded-xl bg-white text-[var(--color-night-100)] placeholder-[var(--color-night-200)]/50 focus:outline-none focus:ring-2 focus:ring-[var(--color-gold-500)] transition-colors ${
                          errors.location ? 'border-red-500' : 'border-[var(--color-sand-300)]'
                        }`}
                        placeholder={fa('مثال: روستای دهکده، استان گلستان', 'e.g., Dehkhadeh Village, Golestan Province')}
                        dir={isFa ? 'rtl' : 'ltr'}
                      />
                    </div>
                    {errors.location && (
                      <p className="mt-1.5 flex items-center gap-1.5 text-sm text-red-500">
                        <AlertCircle className="w-4 h-4" aria-hidden />
                        {errors.location}
                      </p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="village_id" className="block text-sm font-medium text-[var(--color-night-100)] mb-2">
                      {fa('کد روستا', 'Village Code')} <span className="text-red-500">*</span>
                    </label>
                    <div className="relative">
                      <UserPlus className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-night-200)] w-5 h-5" aria-hidden />
                      <input
                        id="village_id"
                        name="village_id"
                        type="text"
                        value={formData.village_id}
                        onChange={handleChange}
                        className={`w-full pl-10 pr-4 py-3 border rounded-xl bg-white text-[var(--color-night-100)] placeholder-[var(--color-night-200)]/50 focus:outline-none focus:ring-2 focus:ring-[var(--color-gold-500)] transition-colors ${
                          errors.village_id ? 'border-red-500' : 'border-[var(--color-sand-300)]'
                        }`}
                        placeholder={fa('کد روستای مورد تایید', 'Approved village code')}
                        dir="ltr"
                      />
                    </div>
                    {errors.village_id && (
                      <p className="mt-1.5 flex items-center gap-1.5 text-sm text-red-500">
                        <AlertCircle className="w-4 h-4" aria-hidden />
                        {errors.village_id}
                      </p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="marketplace_id" className="block text-sm font-medium text-[var(--color-night-100)] mb-2">
                      <Store className="inline h-4 w-4 ml-1" aria-hidden /> {fa('بازارچه', 'Marketplace')} <span className="text-red-500">*</span>
                    </label>
                    <div className="relative">
                      <Store className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-night-200)] w-5 h-5" aria-hidden />
                      <input
                        id="marketplace_id"
                        name="marketplace_id"
                        type="text"
                        value={formData.marketplace_id}
                        onChange={handleChange}
                        className={`w-full pl-10 pr-4 py-3 border rounded-xl bg-white text-[var(--color-night-100)] placeholder-[var(--color-night-200)]/50 focus:outline-none focus:ring-2 focus:ring-[var(--color-gold-500)] transition-colors ${
                          errors.marketplace_id ? 'border-red-500' : 'border-[var(--color-sand-300)]'
                        }`}
                        placeholder={fa('شناسه بازارچه (مثال: mkt_xxx)', 'Marketplace ID (e.g., mkt_xxx)')}
                        dir="ltr"
                      />
                    </div>
                    {errors.marketplace_id && (
                      <p className="mt-1.5 flex items-center gap-1.5 text-sm text-red-500">
                        <AlertCircle className="w-4 h-4" aria-hidden />
                        {errors.marketplace_id}
                      </p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="product_types" className="block text-sm font-medium text-[var(--color-night-100)] mb-2">
                      <Package className="inline h-4 w-4 ml-1" aria-hidden /> {fa('نوع محصولات مورد نظر', 'Product Types')} <span className="text-red-500">*</span>
                    </label>
                    <div className="relative">
                      <Package className="absolute left-3 top-3 text-[var(--color-night-200)] w-5 h-5" aria-hidden />
                      <textarea
                        id="product_types"
                        name="product_types"
                        value={formData.product_types}
                        onChange={handleChange}
                        rows={3}
                        className={`w-full pl-10 pr-4 py-3 border rounded-xl bg-white text-[var(--color-night-100)] placeholder-[var(--color-night-200)]/50 focus:outline-none focus:ring-2 focus:ring-[var(--color-gold-500)] transition-colors resize-none ${
                          errors.product_types ? 'border-red-500' : 'border-[var(--color-sand-300)]'
                        }`}
                        placeholder={fa('محصولاتی که می‌خواهید بفروشید (مثال: گندم، برنج، محصولات دست‌ساز)', 'Products you want to sell (e.g., wheat, rice, handicrafts)')}
                        dir={isFa ? 'rtl' : 'ltr'}
                      />
                    </div>
                    {errors.product_types && (
                      <p className="mt-1.5 flex items-center gap-1.5 text-sm text-red-500">
                        <AlertCircle className="w-4 h-4" aria-hidden />
                        {errors.product_types}
                      </p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="certifications" className="block text-sm font-medium text-[var(--color-night-100)] mb-2">
                      <Award className="inline h-4 w-4 ml-1" aria-hidden /> {fa('گواهینامه‌ها', 'Certifications')} <span className="text-red-500">*</span>
                    </label>
                    <div className="relative">
                      <Award className="absolute left-3 top-3 text-[var(--color-night-200)] w-5 h-5" aria-hidden />
                      <textarea
                        id="certifications"
                        name="certifications"
                        value={formData.certifications}
                        onChange={handleChange}
                        rows={2}
                        className={`w-full pl-10 pr-4 py-3 border rounded-xl bg-white text-[var(--color-night-100)] placeholder-[var(--color-night-200)]/50 focus:outline-none focus:ring-2 focus:ring-[var(--color-gold-500)] transition-colors resize-none ${
                          errors.certifications ? 'border-red-500' : 'border-[var(--color-sand-300)]'
                        }`}
                        placeholder={fa('گواهینامه‌های دارا (مثال: ارگانیک، PGS، تجارت عادلانه)', 'Your certifications (e.g., Organic, PGS, Fair Trade)')}
                        dir={isFa ? 'rtl' : 'ltr'}
                      />
                    </div>
                    {errors.certifications && (
                      <p className="mt-1.5 flex items-center gap-1.5 text-sm text-red-500">
                        <AlertCircle className="w-4 h-4" aria-hidden />
                        {errors.certifications}
                      </p>
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="production_capacity" className="block text-sm font-medium text-[var(--color-night-100)] mb-2">
                        <Truck className="inline h-4 w-4 ml-1" aria-hidden /> {fa('ظرفیت تولید', 'Production Capacity')} <span className="text-red-500">*</span>
                      </label>
                      <div className="relative">
                        <Truck className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-night-200)] w-5 h-5" aria-hidden />
                        <input
                          id="production_capacity"
                          name="production_capacity"
                          type="text"
                          value={formData.production_capacity}
                          onChange={handleChange}
                          className={`w-full pl-10 pr-4 py-3 border rounded-xl bg-white text-[var(--color-night-100)] placeholder-[var(--color-night-200)]/50 focus:outline-none focus:ring-2 focus:ring-[var(--color-gold-500)] transition-colors ${
                            errors.production_capacity ? 'border-red-500' : 'border-[var(--color-sand-300)]'
                          }`}
                          placeholder={fa('مثال: ۵۰۰ کیلوگرم در ماه', 'e.g., 500 kg/month')}
                          dir={isFa ? 'rtl' : 'ltr'}
                        />
                      </div>
                      {errors.production_capacity && (
                        <p className="mt-1.5 flex items-center gap-1.5 text-sm text-red-500">
                          <AlertCircle className="w-4 h-4" aria-hidden />
                          {errors.production_capacity}
                        </p>
                      )}
                    </div>

                    <div>
                      <label htmlFor="years_experience" className="block text-sm font-medium text-[var(--color-night-100)] mb-2">
                        <ClipboardList className="inline h-4 w-4 ml-1" aria-hidden /> {fa('سال‌های تجربه', 'Years of Experience')} <span className="text-red-500">*</span>
                      </label>
                      <div className="relative">
                        <ClipboardList className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-night-200)] w-5 h-5" aria-hidden />
                        <input
                          id="years_experience"
                          name="years_experience"
                          type="text"
                          value={formData.years_experience}
                          onChange={handleChange}
                          className={`w-full pl-10 pr-4 py-3 border rounded-xl bg-white text-[var(--color-night-100)] placeholder-[var(--color-night-200)]/50 focus:outline-none focus:ring-2 focus:ring-[var(--color-gold-500)] transition-colors ${
                            errors.years_experience ? 'border-red-500' : 'border-[var(--color-sand-300)]'
                          }`}
                          placeholder={fa('مثال: ۵ سال', 'e.g., 5 years')}
                          dir={isFa ? 'rtl' : 'ltr'}
                        />
                      </div>
                      {errors.years_experience && (
                        <p className="mt-1.5 flex items-center gap-1.5 text-sm text-red-500">
                          <AlertCircle className="w-4 h-4" aria-hidden />
                          {errors.years_experience}
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="contact_phone" className="block text-sm font-medium text-[var(--color-night-100)] mb-2">
                        <Phone className="inline h-4 w-4 ml-1" aria-hidden /> {fa('شماره تماس', 'Contact Phone')} <span className="text-red-500">*</span>
                      </label>
                      <div className="relative">
                        <Phone className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-night-200)] w-5 h-5" aria-hidden />
                        <input
                          id="contact_phone"
                          name="contact_phone"
                          type="tel"
                          value={formData.contact_phone}
                          onChange={handleChange}
                          className={`w-full pl-10 pr-4 py-3 border rounded-xl bg-white text-[var(--color-night-100)] placeholder-[var(--color-night-200)]/50 focus:outline-none focus:ring-2 focus:ring-[var(--color-gold-500)] transition-colors ${
                            errors.contact_phone ? 'border-red-500' : 'border-[var(--color-sand-300)]'
                          }`}
                          placeholder={fa('مثال: 09121234567', 'e.g., 09121234567')}
                          dir="ltr"
                        />
                      </div>
                      {errors.contact_phone && (
                        <p className="mt-1.5 flex items-center gap-1.5 text-sm text-red-500">
                          <AlertCircle className="w-4 h-4" aria-hidden />
                          {errors.contact_phone}
                        </p>
                      )}
                    </div>

                    <div>
                      <label htmlFor="currency" className="block text-sm font-medium text-[var(--color-night-100)] mb-2">
                        <DollarSign className="inline h-4 w-4 ml-1" aria-hidden /> {fa('ارز', 'Currency')} <span className="text-red-500">*</span>
                      </label>
                      <div className="relative">
                        <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-night-200)] w-5 h-5" aria-hidden />
                        <select
                          id="currency"
                          name="currency"
                          value={formData.currency}
                          onChange={handleChange}
                          className={`w-full pl-10 pr-4 py-3 border rounded-xl bg-white text-[var(--color-night-100)] focus:outline-none focus:ring-2 focus:ring-[var(--color-gold-500)] transition-colors appearance-none ${
                            errors.currency ? 'border-red-500' : 'border-[var(--color-sand-300)]'
                          }`}
                        >
                          <option value="IRR">ریال ایران (IRR)</option>
                          <option value="USD">دلار آمریکا (USD)</option>
                          <option value="EUR">یورو (EUR)</option>
                          <option value="GBP">پوند انگلیس (GBP)</option>
                          <option value="TR">تومان ترکیه (TRY)</option>
                        </select>
                        <MapPin className="pointer-events-none absolute right-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-[var(--color-night-200)]/50" aria-hidden />
                      </div>
                      {errors.currency && (
                        <p className="mt-1.5 flex items-center gap-1.5 text-sm text-red-500">
                          <AlertCircle className="w-4 h-4" aria-hidden />
                          {errors.currency}
                        </p>
                      )}
                    </div>
                  </div>

                  <div>
                    <label htmlFor="social_media" className="block text-sm font-medium text-[var(--color-night-100)] mb-2">
                      <Globe className="inline h-4 w-4 ml-1" aria-hidden /> {fa('شبکه‌های اجتماعی', 'Social Media')} <span className="text-red-500">*</span>
                    </label>
                    <div className="relative">
                      <Globe className="absolute left-3 top-3 text-[var(--color-night-200)] w-5 h-5" aria-hidden />
                      <input
                        id="social_media"
                        name="social_media"
                        type="text"
                        value={formData.social_media}
                        onChange={handleChange}
                        className={`w-full pl-10 pr-4 py-3 border rounded-xl bg-white text-[var(--color-night-100)] placeholder-[var(--color-night-200)]/50 focus:outline-none focus:ring-2 focus:ring-[var(--color-gold-500)] transition-colors ${
                          errors.social_media ? 'border-red-500' : 'border-[var(--color-sand-300)]'
                        }`}
                        placeholder={fa('لینک اینستاگرام، تلگرام و ...', 'e.g., instagram.com/shopname')}
                        dir={isFa ? 'rtl' : 'ltr'}
                      />
                    </div>
                    {errors.social_media && (
                      <p className="mt-1.5 flex items-center gap-1.5 text-sm text-red-500">
                        <AlertCircle className="w-4 h-4" aria-hidden />
                        {errors.social_media}
                      </p>
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="operating_hours" className="block text-sm font-medium text-[var(--color-night-100)] mb-2">
                        <Clock className="inline h-4 w-4 ml-1" aria-hidden /> {fa('ساعات کاری', 'Operating Hours')} <span className="text-red-500">*</span>
                      </label>
                      <div className="relative">
                        <Clock className="absolute left-3 top-3 text-[var(--color-night-200)] w-5 h-5" aria-hidden />
                        <input
                          id="operating_hours"
                          name="operating_hours"
                          type="text"
                          value={formData.operating_hours}
                          onChange={handleChange}
                          className={`w-full pl-10 pr-4 py-3 border rounded-xl bg-white text-[var(--color-night-100)] placeholder-[var(--color-night-200)]/50 focus:outline-none focus:ring-2 focus:ring-[var(--color-gold-500)] transition-colors ${
                            errors.operating_hours ? 'border-red-500' : 'border-[var(--color-sand-300)]'
                          }`}
                          placeholder={fa('مثال: ۸ صبح تا ۶ عصر', 'e.g., 8AM - 6PM')}
                          dir={isFa ? 'rtl' : 'ltr'}
                        />
                      </div>
                      {errors.operating_hours && (
                        <p className="mt-1.5 flex items-center gap-1.5 text-sm text-red-500">
                          <AlertCircle className="w-4 h-4" aria-hidden />
                          {errors.operating_hours}
                        </p>
                      )}
                    </div>

                    <div>
                      <label htmlFor="delivery_area" className="block text-sm font-medium text-[var(--color-night-100)] mb-2">
                        <Navigation className="inline h-4 w-4 ml-1" aria-hidden /> {fa('حوزه تحویل', 'Delivery Area')} <span className="text-red-500">*</span>
                      </label>
                      <div className="relative">
                        <Navigation className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-night-200)] w-5 h-5" aria-hidden />
                        <input
                          id="delivery_area"
                          name="delivery_area"
                          type="text"
                          value={formData.delivery_area}
                          onChange={handleChange}
                          className={`w-full pl-10 pr-4 py-3 border rounded-xl bg-white text-[var(--color-night-100)] placeholder-[var(--color-night-200)]/50 focus:outline-none focus:ring-2 focus:ring-[var(--color-gold-500)] transition-colors ${
                            errors.delivery_area ? 'border-red-500' : 'border-[var(--color-sand-300)]'
                          }`}
                          placeholder={fa('مثال: شهر گرگان و اطراف', 'e.g., Gorgan city and nearby')}
                          dir={isFa ? 'rtl' : 'ltr'}
                        />
                      </div>
                      {errors.delivery_area && (
                        <p className="mt-1.5 flex items-center gap-1.5 text-sm text-red-500">
                          <AlertCircle className="w-4 h-4" aria-hidden />
                          {errors.delivery_area}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {submitStatus === 'success' && (
                <Reveal className="flex items-center gap-3 p-4 bg-green-50 border border-green-200 rounded-xl text-green-800">
                  <Check className="w-6 h-6 flex-shrink-0" aria-hidden />
                  <p className="font-medium">{fa('درخواست شما ارسال شد. در ۲۴ ساعت بررسی خواهد شد.', 'Your application has been submitted. It will be reviewed within 24 hours.')}</p>
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
                {submitStatus === 'loading'
                  ? fa('در حال ثبت...', 'Submitting...')
                  : fa('ثبت‌نام', 'Register')}
              </button>
            </form>

            <Reveal className="mt-12 space-y-4">
              <h3 className="text-lg font-semibold text-[var(--color-night-100)]">
                {fa('شرایط ثبت‌نام', 'Registration Requirements')}
              </h3>
              <div className="grid gap-4 sm:grid-cols-3">
                {requirements.map((req, index) => (
                  <Reveal key={index} delay={index * 0.1} className="p-5 bg-white rounded-xl border border-[var(--color-sand-200)]">
                    <p className="text-[var(--color-night-200)]">{req}</p>
                  </Reveal>
                ))}
              </div>
            </Reveal>

            <Reveal className="mt-8 text-center">
              <Link
                to="/dashboard"
                className="inline-flex items-center gap-2 text-[var(--color-gold-500)] hover:text-[var(--color-gold-600)] font-medium transition-colors"
              >
                <UserPlus className="w-5 h-5" aria-hidden />
                {fa('ورود به داشبورد', 'Go to Dashboard')}
              </Link>
            </Reveal>
          </div>
        </main>
      </div>
    </>
  );
}