import { describe, expect, it } from 'vitest';
import {
  firstInvalidField,
  readLoginFormValues,
  readSignupFormValues,
  toLoginPayload,
  toRegisterPayload,
  validateLogin,
  validateSignup,
} from './validation';

const validSignup = {
  fullName: 'Sara Mirzaei',
  email: 'sara@example.org',
  password: 'correct-horse',
  confirmPassword: 'correct-horse',
  role: 'farmer',
  language: 'fa',
  acceptTerms: true,
  acceptPrivacy: true,
};

describe('login validation', () => {
  it('accepts a well-formed credential pair', () => {
    expect(validateLogin({ email: 'sara@example.org', password: 'correct-horse' })).toEqual({});
  });

  it('reports message keys instead of user-visible copy', () => {
    expect(validateLogin({ email: 'not-an-email', password: 'x' })).toEqual({
      email: 'auth.validation.emailInvalid',
    });
    expect(validateLogin({ email: 'sara@example.org', password: '' })).toEqual({
      password: 'auth.validation.passwordRequired',
    });
  });

  it('points at the first failing field in submission order', () => {
    expect(firstInvalidField(validateLogin({ email: 'nope', password: '' }))).toBe('email');
    expect(firstInvalidField({})).toBeNull();
  });
});

describe('signup validation', () => {
  it('accepts a complete consent-carrying registration', () => {
    expect(validateSignup(validSignup)).toEqual({});
  });

  it('rejects a password confirmation that does not match', () => {
    expect(validateSignup({ ...validSignup, confirmPassword: 'something-else' })).toEqual({
      confirmPassword: 'auth.validation.passwordMismatch',
    });
  });

  it('enforces the password policy shared with the BFF contract', () => {
    expect(validateSignup({ ...validSignup, password: 'short', confirmPassword: 'short' })).toEqual(
      { password: 'auth.validation.passwordMin' },
    );
  });

  it('requires both consent checkboxes and a known role and language', () => {
    expect(
      validateSignup({
        ...validSignup,
        acceptTerms: false,
        acceptPrivacy: false,
        role: 'wizard',
        language: 'de',
      }),
    ).toEqual({
      role: 'auth.validation.roleRequired',
      language: 'auth.validation.languageRequired',
      acceptTerms: 'auth.validation.termsRequired',
      acceptPrivacy: 'auth.validation.privacyRequired',
    });
  });

  it('requires a plausible full name', () => {
    expect(validateSignup({ ...validSignup, fullName: '  ' })).toEqual({
      fullName: 'auth.validation.fullNameRequired',
    });
  });
});

describe('form value reading', () => {
  it('trims the email like the BFF contract and keeps the password verbatim', () => {
    const data = new FormData();
    data.append('email', '  sara@example.org  ');
    data.append('password', ' correct-horse ');

    const values = readLoginFormValues(data);
    expect(values).toEqual({ email: 'sara@example.org', password: ' correct-horse ' });
    expect(toLoginPayload(values)).toEqual({
      email: 'sara@example.org',
      password: ' correct-horse ',
    });
  });

  it('maps the signup form into the BFF register contract', () => {
    const data = new FormData();
    data.append('fullName', '  Sara Mirzaei  ');
    data.append('email', '  sara@example.org  ');
    data.append('password', 'correct-horse');
    data.append('confirmPassword', 'correct-horse');
    data.append('role', 'researcher');
    data.append('language', 'en');
    data.append('acceptTerms', 'on');
    data.append('acceptPrivacy', 'on');

    const payload = toRegisterPayload(readSignupFormValues(data));
    expect(payload).toEqual({
      email: 'sara@example.org',
      full_name: 'Sara Mirzaei',
      password: 'correct-horse',
      role: 'researcher',
      language: 'en',
      accept_tos: true,
      accept_privacy: true,
    });
  });
});
