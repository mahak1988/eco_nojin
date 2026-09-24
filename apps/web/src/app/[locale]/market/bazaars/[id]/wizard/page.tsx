'use client';

import { useState, useCallback } from 'react';
import { useParams, useRouter, usePathname } from 'next/navigation';
import { FormProvider, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
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
import { WIZARD_TOTAL_STEPS, stepLabels } from '@/components/BazaarEstablishmentWizard';
import { BazaarStepRenderer } from '@/components/market/BazaarStepRenderer';

const TOTAL_STEPS = WIZARD_TOTAL_STEPS;

export type WizardStepStatus = 'pending' | 'active' | 'completed' | 'error';

export default function BazaarWizardPage() {
  const params = useParams();
  const locale = params.locale as string;
  const id = params.id as string;
  const router = useRouter();
  const pathname = usePathname();

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
      step7: { verifiedBy: '', verificationDate: '', verificationNotes: '' },
      step8: { registrationNumber: '', registrationDate: '', regulatorId: '', systemId: '' },
      step9: { launchDate: '', initialStockCount: 0, operationalNotes: '' },
      step10: { oversightSchedule: '', reviewCycleMonths: 12, supportContact: '' },
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

  const watchedStep1 = watch('step1');

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
    if (step > currentStep && stepStatuses[step - 1] !== 'completed') return;
    setCurrentStep(step);
  }, [currentStep, stepStatuses]);

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
      const result = await apiPost('/api/v1/bazaars/establish', { ...data, tenant_id: id });
      setSubmitResult(result);
      if (result.ok) {
        router.push(`/${locale}/market/bazaars/${id}`);
      }
    } catch (err) {
      setSubmitResult({ ok: false, error: String(err), status: 0 });
    } finally {
      setIsSubmitting(false);
    }
  }, [getValues, id, locale, router]);

  const getStepStatusIcon = (status: WizardStepStatus) => {
    switch (status) {
      case 'completed': return '✓';
      case 'error': return '✗';
      case 'active': return '●';
      default: return '○';
    }
  };

  const backUrl = `/${locale}/market/bazaars/${id}`;

  return (
    <main id="main" className="min-h-dvh">
      <div className="mx-auto max-w-5xl px-6 pb-12 pt-6">
        <header className="mb-8">
          <nav className="mb-4">
            <a
              href={backUrl}
              className="text-sm text-ink-soft hover:text-ink underline"
            >
              ← {locale === 'fa' ? 'بازگشت به بازارچه' : 'Back to Bazaar'}
            </a>
          </nav>
          <ProvenanceStamp source="bazaar-establishment-wizard" label="تأسیس بازارچه — 10 گام">
            <h1 className="display text-3xl font-bold text-ink sm:text-4xl">
              {locale === 'fa' ? 'معاونت تأسیس بازارچه' : 'Bazaar Establishment Wizard'}
            </h1>
          </ProvenanceStamp>
        </header>

        <Card className="mb-6">
          <p className="text-ink-soft">
            {locale === 'fa'
              ? 'این جادوگر ۱۰-مرحله‌ای شما را در فرآیند تأسیس بازارچه نهادی راهنمایی می‌کند. هر گام به‌صورت خودکار ذخیره می‌شود.'
              : 'This 10-step wizard guides you through institutional bazaar establishment. Each step auto-saves.'}
          </p>
        </Card>

        {/* Sticky step list */}
        <nav
          className="sticky top-0 z-10 bg-background/95 backdrop-blur border-b border-line py-3 px-4 mb-6"
          aria-label="Wizard steps"
        >
          <ol className="flex gap-1 overflow-x-auto text-xs">
            {Array.from({ length: TOTAL_STEPS }, (_, i) => {
              const step = i + 1;
              const status = stepStatuses[step];
              const isActive = step === currentStep;
              const canNavigate = step <= currentStep || status === 'completed';
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
                    disabled={!canNavigate}
                  >
                    <span aria-hidden="true">{getStepStatusIcon(status)}</span>
                    <span className="num">{step}</span>
                    <span className="hidden sm:inline">{locale === 'fa' ? stepLabels[i].fa : stepLabels[i].en}</span>
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
          <Button
            type="button"
            variant="ghost"
            onClick={prevStep}
            disabled={currentStep === 1}
          >
            {locale === 'fa' ? '↩ گام قبلی' : '← Previous'}
          </Button>

          <span className="text-xs text-ink-soft num">
            {locale === 'fa'
              ? `گام ${currentStep} از ${TOTAL_STEPS}`
              : `Step ${currentStep} of ${TOTAL_STEPS}`}
          </span>

          {currentStep < TOTAL_STEPS ? (
            <Button type="button" onClick={nextStep}>
              {locale === 'fa' ? 'گام بعدی →' : 'Next →'}
            </Button>
          ) : (
            <Button
              type="button"
              onClick={handleSubmit}
              disabled={isSubmitting || !isValid}
            >
              {isSubmitting
                ? locale === 'fa'
                  ? 'در حال ثبت...'
                  : 'Submitting...'
                : locale === 'fa'
                  ? 'تأسیس بازارچه ✓'
                  : 'Establish ✓'}
            </Button>
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
    </main>
  );
}