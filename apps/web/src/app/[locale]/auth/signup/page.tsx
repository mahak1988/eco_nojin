'use client';

import { useLocale } from 'next-intl';
import { type FormEvent, useRef, useState } from 'react';
import { AuthErrorAlert } from '@/components/auth/AuthErrorAlert';
import { AuthShell } from '@/components/auth/AuthShell';
import type { AuthErrorKey } from '@/components/auth/errors';
import { errorDetail, toAuthErrorKey } from '@/components/auth/errors';
import { PasswordField } from '@/components/auth/PasswordField';
import { accountLanguageKey, roleLabelKey } from '@/components/auth/role-label';
import { useAuthMessage } from '@/components/auth/useAuthMessage';
import { ValidationSummary } from '@/components/auth/ValidationSummary';
import {
  ACCOUNT_LANGUAGES,
  firstInvalidField,
  REGISTER_ROLES,
  readSignupFormValues,
  toRegisterPayload,
  validateSignup,
} from '@/components/auth/validation';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { useAuth } from '@/components/providers/AuthProvider';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Link, useRouter } from '@/i18n/navigation';

type SignupFieldErrors = ReturnType<typeof validateSignup>;

const CONSENT_FIELDS = [
  { name: 'acceptTerms', labelKey: 'auth.signup.acceptTerms', errorId: 'acceptTerms-error' },
  { name: 'acceptPrivacy', labelKey: 'auth.signup.acceptPrivacy', errorId: 'acceptPrivacy-error' },
] as const;

export default function SignupPage() {
  const t = useAuthMessage();
  const locale = useLocale();
  const router = useRouter();
  const { user, loading: sessionLoading, register } = useAuth();
  const formRef = useRef<HTMLFormElement>(null);
  const [errors, setErrors] = useState<SignupFieldErrors>({});
  const [submitting, setSubmitting] = useState(false);
  const [failure, setFailure] = useState<{ messageKey: AuthErrorKey; detail?: string } | null>(
    null,
  );

  const focusField = (name: string) => {
    formRef.current?.querySelector<HTMLElement>(`[name="${name}"]`)?.focus();
  };

  const initialLanguage = ACCOUNT_LANGUAGES.find((value) => value === locale) ?? 'fa';

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFailure(null);

    const values = readSignupFormValues(new FormData(event.currentTarget));
    const found = validateSignup(values);
    setErrors(found);

    const invalid = firstInvalidField(found);
    if (invalid) {
      focusField(invalid);
      return;
    }

    setSubmitting(true);
    try {
      await register(toRegisterPayload(values));
      router.replace('/home');
    } catch (error) {
      setFailure({ messageKey: toAuthErrorKey(error), detail: errorDetail(error) });
      setSubmitting(false);
    }
  }

  const footer = (
    <p>
      {t('auth.signup.hasAccount')}{' '}
      <Link href="/auth/login" className="text-water hover:underline">
        {t('auth.signup.signInInstead')}
      </Link>
    </p>
  );

  if (user) {
    return (
      <AuthShell title={t('auth.signup.title')} lead={t('auth.signup.lead')} footer={footer}>
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
    <AuthShell title={t('auth.signup.title')} lead={t('auth.signup.lead')} footer={footer}>
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
          name="fullName"
          type="text"
          label={t('auth.signup.fullName')}
          autoComplete="name"
          maxLength={100}
          required
          aria-invalid={errors.fullName ? true : undefined}
          error={errors.fullName ? t(errors.fullName) : undefined}
        />

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
          autoComplete="new-password"
          minLength={8}
          error={errors.password ? t(errors.password) : undefined}
        />

        <PasswordField
          name="confirmPassword"
          label={t('auth.signup.passwordConfirm')}
          autoComplete="new-password"
          minLength={8}
          error={errors.confirmPassword ? t(errors.confirmPassword) : undefined}
        />

        <Select
          name="role"
          label={t('auth.signup.accountType')}
          defaultValue="regular"
          required
          aria-invalid={errors.role ? true : undefined}
          error={errors.role ? t(errors.role) : undefined}
        >
          {REGISTER_ROLES.map((role) => (
            <option key={role} value={role}>
              {t(roleLabelKey(role) ?? 'auth.roles.regular')}
            </option>
          ))}
        </Select>

        <Select
          name="language"
          label={t('auth.signup.interfaceLanguage')}
          defaultValue={initialLanguage}
          required
          aria-invalid={errors.language ? true : undefined}
          error={errors.language ? t(errors.language) : undefined}
        >
          {ACCOUNT_LANGUAGES.map((language) => (
            <option key={language} value={language}>
              {t(accountLanguageKey(language) ?? 'auth.languages.fa')}
            </option>
          ))}
        </Select>

        <fieldset className="flex flex-col gap-3">
          <legend className="field-label">{t('auth.signup.consent')}</legend>
          {CONSENT_FIELDS.map((field) => {
            const consentError = errors[field.name];
            return (
              <div key={field.name}>
                <label htmlFor={field.name} className="flex items-start gap-2 text-sm text-ink">
                  <input
                    id={field.name}
                    name={field.name}
                    type="checkbox"
                    className="mt-1 size-4 shrink-0 rounded border-line"
                    aria-invalid={consentError ? true : undefined}
                    aria-describedby={consentError ? field.errorId : undefined}
                  />
                  <span>{t(field.labelKey)}</span>
                </label>
                {consentError ? (
                  <p id={field.errorId} className="mt-1 ps-6 text-sm text-error">
                    {t(consentError)}
                  </p>
                ) : null}
              </div>
            );
          })}
          <p className="text-xs text-ink-soft">
            <Link href="/legal" className="text-water hover:underline">
              {t('auth.common.termsOfService')} · {t('auth.common.privacyPolicy')}
            </Link>
          </p>
        </fieldset>

        <Button type="submit" size="lg" loading={submitting} disabled={sessionLoading}>
          {submitting ? t('auth.signup.pending') : t('auth.signup.submit')}
        </Button>

        {sessionLoading ? (
          <p role="status" className="text-xs text-ink-soft">
            {t('auth.common.checkingSession')}
          </p>
        ) : null}
      </form>

      <ProvenanceStamp
        className="mt-8"
        source={t('auth.signup.source')}
        method={t('auth.signup.method')}
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
