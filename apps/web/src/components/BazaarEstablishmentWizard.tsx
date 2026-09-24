'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { useCallback, useState } from 'react';
import { FormProvider, useForm } from 'react-hook-form';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { type ApiResult, apiPost } from '@/lib/api/client';
import {
  type BazaarFormInput,
  bazaarEstablishmentSchema,
  step1Schema,
  step2Schema,
  step3Schema,
  step4Schema,
  step5Schema,
  step6Schema,
  step7Schema,
  step8Schema,
  step9Schema,
  step10Schema,
} from '@/lib/validation/bazaar-establishment';

const TOTAL_STEPS = 10;

const stepLabels = [
  { fa: 'مشخصات بازارچه', en: 'Bazaar Identity' },
  { fa: 'محدوده جغرافیایی', en: 'Geographic Boundary' },
  { fa: 'هیئت مؤسس ۵ نفره', en: 'Founding Board (5)' },
  { fa: 'قوانین و ضوابط', en: 'Rules & Regulations' },
  { fa: 'فروشندگان', en: 'Vendors & Stores' },
  { fa: 'امضای دیجیتال ۵ طرف', en: '5-Party Digital Signatures' },
  { fa: 'اعتبارسنجی', en: 'Verification' },
  { fa: 'ثبت رسمی', en: 'Official Registration' },
  { fa: 'راه‌اندازی', en: 'Operational Launch' },
  { fa: 'نظارت و پشتیبانی', en: 'Oversight & Support' },
];

export type WizardStepStatus = 'pending' | 'active' | 'completed' | 'error';

export interface BazaarEstablishmentWizardProps {
  locale: string;
  tenantId?: string;
  onComplete?: (data: BazaarFormInput) => void;
}

export function BazaarEstablishmentWizard({
  locale,
  tenantId,
  onComplete,
}: BazaarEstablishmentWizardProps) {
  const methods = useForm<BazaarFormInput>({
    resolver: zodResolver(bazaarEstablishmentSchema),
    mode: 'onChange',
    defaultValues: {
      step1: {
        name: '',
        code: '',
        bazaarType: 'rural',
        description: '',
        address: '',
        latitude: undefined,
        longitude: undefined,
      },
      step2: { boundingBox: {}, areaHa: undefined, polygonGeojson: undefined },
      step3: { trustees: [] },
      step4: { storeCount: 0 },
      step5: { vendorIds: [], expectedStoreCount: 0, vendorCategories: [] },
      step6: { signatures: [] },
      step7: {},
      step8: {},
      step9: {},
      step10: {},
    },
  });

  const {
    watch,
    trigger,
    setValue,
    getValues,
    formState: { errors, isValid },
  } = methods;

  const [currentStep, setCurrentStep] = useState(1);
  const [stepStatuses, setStepStatuses] = useState<Record<number, WizardStepStatus>>(() =>
    Array.from({ length: TOTAL_STEPS }, (_, i) => ({
      [i + 1]: 'pending' as WizardStepStatus,
    })).reduce((a, b) => ({ ...a, ...b }), {}),
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitResult, setSubmitResult] = useState<ApiResult<unknown> | null>(null);

  const watchedStep1 = watch('step1') as { name?: string } | undefined;

  const markStep = useCallback((step: number, status: WizardStepStatus) => {
    setStepStatuses((prev) => ({ ...prev, [step]: status }));
  }, []);

  const validateCurrentStep = useCallback(async () => {
    const schemaMap = [
      null,
      step1Schema,
      step2Schema,
      step3Schema,
      step4Schema,
      step5Schema,
      step6Schema,
      step7Schema,
      step8Schema,
      step9Schema,
      step10Schema,
    ];
    const schema = schemaMap[currentStep];
    if (!schema) return true;
    const data = getValues(`step${currentStep}` as keyof BazaarFormInput);
    const result = await schema.safeParseAsync(data);
    if (result.success) {
      markStep(currentStep, 'completed');
      return true;
    } else {
      markStep(currentStep, 'error');
      await trigger(`step${currentStep}` as keyof BazaarFormInput);
      return false;
    }
  }, [currentStep, trigger, markStep, getValues]);

  const goToStep = useCallback((step: number) => {
    if (step < 1 || step > TOTAL_STEPS) return;
    setCurrentStep(step);
  }, []);

  const nextStep = useCallback(async () => {
    const ok = await validateCurrentStep();
    if (ok && currentStep < TOTAL_STEPS) {
      setCurrentStep((s) => Math.min(s + 1, TOTAL_STEPS));
    }
  }, [validateCurrentStep, currentStep]);

  const prevStep = useCallback(() => {
    setCurrentStep((s) => Math.max(s - 1, 1));
  }, []);

  const handleSubmit = useCallback(async () => {
    setIsSubmitting(true);
    try {
      const data = getValues();
      const result = await apiPost('/api/v1/bazaars/establish', { ...data, tenant_id: tenantId });
      setSubmitResult(result);
      if (result.ok && onComplete) {
        onComplete(data);
      }
    } catch (err) {
      setSubmitResult({ ok: false, error: String(err), status: 0 });
    } finally {
      setIsSubmitting(false);
    }
  }, [getValues, tenantId, onComplete]);

  const getStepStatusIcon = (status: WizardStepStatus) => {
    switch (status) {
      case 'completed':
        return '✓';
      case 'error':
        return '✗';
      case 'active':
        return '●';
      default:
        return '○';
    }
  };

  return (
    <div
      className="bazaar-wizard"
      data-locale={locale}
      dir={locale === 'fa' || locale === 'ar' ? 'rtl' : 'ltr'}
    >
      <ProvenanceStamp source="bazaar-establishment-wizard" label="تأسیس بازارچه — 10 گام">
        <h2 className="text-xl font-bold text-ink">
          {locale === 'fa' ? 'تأسیس بازارچه' : 'Establish Bazaar'}
        </h2>
      </ProvenanceStamp>

      {/* Sticky step list */}
      <nav
        className="sticky top-0 z-10 bg-background/95 backdrop-blur border-b border-line py-3 px-4"
        aria-label="Wizard steps"
      >
        <ol className="flex gap-1 overflow-x-auto text-xs">
          {Array.from({ length: TOTAL_STEPS }, (_, i) => {
            const step = i + 1;
            const status = stepStatuses[step];
            const isActive = step === currentStep;
            return (
              <li key={step}>
                <button
                  type="button"
                  onClick={() => goToStep(step)}
                  className={`flex items-center gap-1 px-3 py-1.5 rounded border whitespace-nowrap transition-colors
                    ${isActive ? 'border-primary bg-primary/10 text-primary' : ''}
                    ${!isActive && status === 'completed' ? 'border-success/30 bg-success/5 text-success' : ''}
                    ${!isActive && status === 'error' ? 'border-error/30 bg-error/5 text-error' : ''}
                    ${!isActive && status === 'pending' ? 'border-line bg-surface text-ink-soft hover:border-ink-soft' : ''}
                  `}
                  aria-current={isActive ? 'step' : undefined}
                  disabled={step > currentStep && status !== 'completed'}
                >
                  <span aria-hidden="true">{getStepStatusIcon(status)}</span>
                  <span className="num">{step}</span>
                  <span className="hidden sm:inline">{stepLabels[i].fa}</span>
                </button>
              </li>
            );
          })}
        </ol>
      </nav>

      {/* Step content area */}
      <div className="p-4 md:p-6">
        <FormProvider {...methods}>
          <BazaarStepRenderer step={currentStep} locale={locale} watchedStep1={watchedStep1} />
        </FormProvider>
      </div>

      {/* Navigation */}
      <div className="flex items-center justify-between p-4 border-t border-line">
        <button
          type="button"
          onClick={prevStep}
          disabled={currentStep === 1}
          className="px-4 py-2 rounded border border-line text-ink-soft disabled:opacity-40 hover:text-ink"
        >
          {locale === 'fa' ? '↩ گام قبلی' : '← Previous'}
        </button>

        <span className="text-xs text-ink-soft num">
          {locale === 'fa'
            ? `گام ${currentStep} از ${TOTAL_STEPS}`
            : `Step ${currentStep} of ${TOTAL_STEPS}`}
        </span>

        {currentStep < TOTAL_STEPS ? (
          <button
            type="button"
            onClick={nextStep}
            className="px-4 py-2 rounded bg-primary text-white hover:opacity-90"
          >
            {locale === 'fa' ? 'گام بعدی →' : 'Next →'}
          </button>
        ) : (
          <button
            type="button"
            onClick={handleSubmit}
            disabled={isSubmitting || !isValid}
            className="px-4 py-2 rounded bg-success text-white hover:opacity-90 disabled:opacity-40"
          >
            {isSubmitting
              ? locale === 'fa'
                ? 'در حال ثبت...'
                : 'Submitting...'
              : locale === 'fa'
                ? 'تأسیس بازارچه ✓'
                : 'Establish ✓'}
          </button>
        )}
      </div>

      {submitResult && !submitResult.ok && (
        <div
          className="m-4 p-3 border border-error/30 bg-error/5 text-error text-sm rounded"
          role="alert"
        >
          {submitResult.error}
        </div>
      )}
      {submitResult && submitResult.ok && (
        <div
          className="m-4 p-3 border border-success/30 bg-success/5 text-success text-sm rounded"
          role="status"
        >
          {locale === 'fa' ? 'بازارچه با موفقیت تأسیس شد.' : 'Bazaar established successfully.'}
        </div>
      )}
    </div>
  );
}

// Step 7 — Placeholder for step content; each step is a scaffold for Phase 3
function BazaarStepRenderer({
  step,
  locale,
  watchedStep1,
}: {
  step: number;
  locale: string;
  watchedStep1: { name?: string } | undefined;
}) {
  const stepTitle = stepLabels[step - 1];
  return (
    <fieldset className="space-y-4" aria-labelledby={`step-${step}-legend`}>
      <legend id={`step-${step}-legend`} className="text-lg font-semibold text-ink">
        <span className="num text-sm text-ink-faint mr-2">{step}</span>
        {locale === 'fa' ? stepTitle.fa : stepTitle.en}
      </legend>
      <div className="card p-5 min-h-[120px]">
        <p className="text-sm text-ink-soft">
          {locale === 'fa'
            ? `این قسمت مرحلهٔ ${step} — «${stepTitle.fa}» — اسکافلد است. پیاده‌سازی کامل در فاز ۳ تحویل داده می‌شود.`
            : `Step ${step}: "${stepTitle.en}" — scaffold. Full implementation delivered in Phase 3.`}
        </p>
        {step === 1 && watchedStep1 && (
          <div className="mt-3 text-xs text-ink-faint">
            {locale === 'fa'
              ? `پیش‌نمایش: ${watchedStep1.name || '...'}`
              : `Preview: ${watchedStep1.name || '...'}`}
          </div>
        )}
      </div>
    </fieldset>
  );
}

export const WIZARD_TOTAL_STEPS = TOTAL_STEPS;
export { stepLabels };
