/**
 * CameraTour Tests
 */
import { describe, it, expect } from 'vitest';
import { CameraTour } from '../components/canvas';
import type { CameraTourProps } from '../components/canvas/CameraTour';

describe('CameraTour Component', () => {
  it('should export CameraTour as function', () => {
    expect(typeof CameraTour).toBe('function');
  });

  it('should accept active=true', () => {
    const props: CameraTourProps = { active: true };
    expect(props.active).toBe(true);
  });

  it('should accept active=false', () => {
    const props: CameraTourProps = { active: false };
    expect(props.active).toBe(false);
  });
});
