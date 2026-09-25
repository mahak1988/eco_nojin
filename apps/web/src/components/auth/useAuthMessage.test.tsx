import { cleanup, render, screen } from '@testing-library/react';
import { NextIntlClientProvider } from 'next-intl';
import { afterEach, describe, expect, it, vi } from 'vitest';
import de from '../../../messages/de.json';
import en from '../../../messages/en.json';
import fa from '../../../messages/fa.json';
import { MachineTranslationNotice } from './MachineTranslationNotice';
import { ValidationSummary } from './ValidationSummary';

afterEach(() => {
  cleanup();
});

describe('useAuthMessage resolution', () => {
  it('renders the catalogue string for an absolute auth key', () => {
    render(
      <NextIntlClientProvider locale="en" messages={en}>
        <ValidationSummary
          errors={{ email: 'auth.validation.emailInvalid' }}
          onFocusField={vi.fn()}
        />
      </NextIntlClientProvider>,
    );

    const alert = screen.getByRole('alert');
    expect(alert.textContent).toContain('Review the highlighted fields');
    expect(alert.textContent).toContain('Enter a valid email address.');
    expect(alert.textContent).not.toContain('auth.validation');
  });

  it('moves focus to the field behind a failed entry', () => {
    const onFocusField = vi.fn();
    render(
      <NextIntlClientProvider locale="fa" messages={fa}>
        <ValidationSummary
          errors={{ password: 'auth.validation.passwordMin' }}
          onFocusField={onFocusField}
        />
      </NextIntlClientProvider>,
    );

    screen.getByRole('button', { name: 'دست‌کم ۸ نویسه به کار ببرید.' }).click();
    expect(onFocusField).toHaveBeenCalledWith('password');
  });
});

describe('MachineTranslationNotice', () => {
  it('stays hidden for a human-authored catalogue', () => {
    const { container } = render(
      <NextIntlClientProvider locale="fa" messages={fa}>
        <MachineTranslationNotice />
      </NextIntlClientProvider>,
    );

    expect(container.textContent).toBe('');
  });

  it('labels a machine-translated catalogue honestly', () => {
    render(
      <NextIntlClientProvider locale="de" messages={de}>
        <MachineTranslationNotice />
      </NextIntlClientProvider>,
    );

    expect(screen.getByText(/maschinell übersetzt/)).not.toBeNull();
  });
});
