/**
 * Tiny assertion helpers for non-null invariants.
 * Avoid `!` non-null assertions in app code.
 */

export function assertDefined<T>(value: T | null | undefined, message = 'Value is null/undefined'): T {
  if (value === null || value === undefined) {
    throw new Error(message);
  }
  return value;
}

export function assert(condition: unknown, message = 'Assertion failed'): asserts condition {
  if (!condition) {
    throw new Error(message);
  }
}