'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { useAuthMessage } from './useAuthMessage';

export interface PasswordFieldProps {
  name: string;
  label: string;
  autoComplete: string;
  error?: string;
  required?: boolean;
  minLength?: number;
}

/**
 * Password input with a localized show/hide toggle. The toggle keeps a pressed
 * state and an accessible name built from the field label, so the two password
 * controls of the signup form stay distinguishable.
 */
export function PasswordField({
  name,
  label,
  autoComplete,
  error,
  required = true,
  minLength,
}: PasswordFieldProps) {
  const t = useAuthMessage();
  const [visible, setVisible] = useState(false);

  return (
    <div className="grid grid-cols-[minmax(0,1fr)_auto] items-end gap-2">
      <Input
        name={name}
        type={visible ? 'text' : 'password'}
        label={label}
        autoComplete={autoComplete}
        error={error}
        required={required}
        minLength={minLength}
        maxLength={128}
        aria-invalid={error ? true : undefined}
      />
      <Button
        variant="ghost"
        size="sm"
        aria-pressed={visible}
        aria-label={
          visible
            ? t('auth.common.hidePasswordFor', { field: label })
            : t('auth.common.showPasswordFor', { field: label })
        }
        onClick={() => setVisible((current) => !current)}
        className="whitespace-nowrap"
      >
        {visible ? t('auth.common.hidePassword') : t('auth.common.showPassword')}
      </Button>
    </div>
  );
}
