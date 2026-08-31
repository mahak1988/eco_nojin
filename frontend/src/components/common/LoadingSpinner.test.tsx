import { render } from '@testing-library/react';
// اگر «export default» بود:
import LoadingSpinner from './LoadingSpinner';
// اگر «export function LoadingSpinner» بود، خط بالا را عوض کنید به:
// import { LoadingSpinner } from './LoadingSpinner'

test('LoadingSpinner بدون کرش رندر می‌شود', () => {
  const { container } = render(<LoadingSpinner />);
  expect(container.firstChild).not.toBeNull();
});
