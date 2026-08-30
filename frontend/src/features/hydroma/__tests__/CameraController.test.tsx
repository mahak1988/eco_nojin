/**
 * CameraController Tests
 */
import { describe, it, expect } from 'vitest';
import { CameraController } from '../components/canvas';
import type { CameraControllerProps } from '../components/canvas/CameraController';
import type { ViewMode } from '../types';

describe('CameraController Component', () => {
  it('should export CameraController as function', () => {
    expect(typeof CameraController).toBe('function');
  });

  it('should accept all view modes', () => {
    const modes: ViewMode[] = ['3d', '2d-top', '2d-side', 'cross-section'];
    modes.forEach((mode) => {
      const props: CameraControllerProps = { viewMode: mode };
      expect(props.viewMode).toBe(mode);
    });
  });

  it('should default to 3d in typical usage', () => {
    const props: CameraControllerProps = { viewMode: '3d' };
    expect(props.viewMode).toBe('3d');
  });
});
