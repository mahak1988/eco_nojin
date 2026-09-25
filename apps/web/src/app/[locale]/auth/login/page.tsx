'use client';

import { type FormEvent, useRef, useState } from 'react';
import { AuthErrorAlert } from '@/components/auth/AuthErrorAlert';
import { AuthShell } from '@/components/auth/AuthShell';
import type { AuthErrorKey } from '@/components/auth/errors';
import { errorDetail, toAuthErrorKey } from '@/components/auth/errors';
import { PasswordField } from '@/components/auth/PasswordField';
import { useAuthMessage } from '@/components/auth/useAuthMessage';
import { ValidationSummary } from '@/components/auth/ValidationSummary';
import {
  firstInvalidField,
  readLoginFormValues,
  toLoginPayload,
  validateLogin,
} from '@/components/auth/validation';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { useAuth } from '@/components/providers/AuthProvider';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Link, useRouter } from '@/i18n/navigation';

type LoginFieldErrors = ReturnType<typeof validateLogin>;

export default function LoginPage() {
  const t = useAuthMessage();
  const router = useRouter();
  const { user, loading: sessionLoading, login } = useAuth();
  const formRef = useRef<HTMLFormElement>(null);
  const [errors, setErrors] = useState<LoginFieldErrors>({});
  const [submitting, setSubmitting] = useState(false);
  const [failure, setFailure] = useState<{ messageKey: AuthErrorKey; detail?: string } | null>(
    null,
  );

  const focusField = (name: string) => {
    formRef.current?.querySelector<HTMLElement>(`[name="${name}"]`)?.focus();
  };

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFailure(null);

    const values = readLoginFormValues(new FormData(event.currentTarget));
    const found = validateLogin(values);
    setErrors(found);

    const invalid = firstInvalidField(found);
    if (invalid) {
      focusField(invalid);
      return;
    }

    setSubmitting(true);
    try {
      await login(toLoginPayload(values));
      router.replace('/home');
    } catch (error) {
      setFailure({ messageKey: toAuthErrorKey(error), detail: errorDetail(error) });
      setSubmitting(false);
    }
  }

  const footer = (
    <p>
      {t('auth.login.noAccount')}{' '}
      <Link href="/auth/signup" className="text-water hover:underline">
        {t('auth.login.createAccount')}
      </Link>
    </p>
  );

  if (user) {
    return (
      <AuthShell title={t('auth.login.title')} lead={t('auth.login.lead')} footer={footer}>
        <div className="card p-4">
          <p className="text-sm font-semibold text-ink">{t('auth.common.alreadySignedIn')}</p>
          <p className="mt-1 truncate text-sm text-ink-soft" dir="auto">
            {user.full_name?.trim() || user.email}
          </p>
          <div className="mt-4 flex flex-wrap gap-3">
            <Link href="/account/session" className="text-sm text-water hover:underline">
              {t('auth.common.sessionDetails')}
            </Link>
            <Link href="/home" className="text-sm text-water hover:underline">
              {t('auth.common.backToHome')}
            </Link>
          </div>
        </div>
      </AuthShell>
    );
  }

  return (
    <AuthShell title={t('auth.login.title')} lead={t('auth.login.lead')} footer={footer}>
      <form
        ref={formRef}
        noValidate
        aria-busy={submitting}
        onSubmit={handleSubmit}
        className="flex flex-col gap-4"
      >
        {failure ? (
          <AuthErrorAlert messageKey={failure.messageKey} detail={failure.detail} />
        ) : null}
        <ValidationSummary errors={errors} onFocusField={focusField} />

        <Input
          name="email"
          type="email"
          label={t('auth.common.email')}
          autoComplete="email"
          inputMode="email"
          dir="ltr"
          maxLength={254}
          required
          aria-invalid={errors.email ? true : undefined}
          error={errors.email ? t(errors.email) : undefined}
        />

        <PasswordField
          name="password"
          label={t('auth.common.password')}
          autoComplete="current-password"
          error={errors.password ? t(errors.password) : undefined}
        />

        <Button type="submit" size="lg" loading={submitting} disabled={sessionLoading}>
          {submitting ? t('auth.login.pending') : t('auth.login.submit')}
        </Button>

        {sessionLoading ? (
          <p role="status" className="text-xs text-ink-soft">
            {t('auth.common.checkingSession')}
          </p>
        ) : null}
      </form>

      <ProvenanceStamp
        className="mt-8"
        source={t('auth.login.source')}
        method={t('auth.login.method')}
        label={t('auth.login.transport')}
        labels={{
          heading: t('auth.common.provenance.heading'),
          source: t('auth.common.provenance.source'),
          method: t('auth.common.provenance.method'),
        }}
      />
    </AuthShell>
  );
}
