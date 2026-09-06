import { Link } from '@tanstack/react-router';
import { Button, EmptyState } from '@eco/ui';

export function NotFoundPage() {
  return (
    <EmptyState
      title="404 — page not found"
      description="The page you were looking for has moved or never existed."
      action={
        <Link to="/" className="inline-flex items-center justify-center rounded-md bg-brand-600 px-6 py-2 text-sm font-medium text-white">
          Go home
        </Link>
      }
    />
  );
}