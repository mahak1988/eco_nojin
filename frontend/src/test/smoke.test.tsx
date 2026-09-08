import { render, screen } from '@testing-library/react';
import { Suspense } from 'react';
import { MemoryRouter } from 'react-router-dom';
import { LanguageProvider } from '../i18n/LanguageContext';
import { AppShell } from '../App';
import RouteFallback from '../components/ui/RouteFallback';

function renderShell(initialPath: string) {
  return render(
    <LanguageProvider>
      <MemoryRouter initialEntries={[initialPath]}>
        <Suspense fallback={<RouteFallback />}>
          <AppShell />
        </Suspense>
      </MemoryRouter>
    </LanguageProvider>,
  );
}

describe('AppShell', () => {
  it('renders the brand name in the navbar on the home route', async () => {
    renderShell('/');
    const logos = await screen.findAllByText('اکو نوژین');
    expect(logos.length).toBeGreaterThan(0);
  });

  it('renders the platform page heading', async () => {
    renderShell('/platform');
    expect(
      await screen.findByRole('heading', { level: 1, name: /ماژول‌های اکو نوژین/ }),
    ).toBeInTheDocument();
  });

  it('renders the hero title on the home route', async () => {
    renderShell('/');
    expect(await screen.findByText(/تصمیمِ میدانی/)).toBeInTheDocument();
  });

  it('renders blog posts about the project', async () => {
    renderShell('/blog');
    expect(
      await screen.findByRole('heading', { level: 2, name: 'چرا اکو نوژین؟' }),
    ).toBeInTheDocument();
  });

  it('renders the privacy policy sections', async () => {
    renderShell('/privacy');
    expect(
      await screen.findByRole('heading', { level: 1, name: 'حریم خصوصی' }),
    ).toBeInTheDocument();
    expect(await screen.findByText(/فروخته نمی‌شود/)).toBeInTheDocument();
  });

  it('renders the FAQ items', async () => {
    renderShell('/faq');
    expect(
      await screen.findByRole('heading', { level: 1, name: 'پاسخ پرسش‌های پرتکرار' }),
    ).toBeInTheDocument();
    expect(await screen.findByText(/اکوکویین توکن کاربردی/)).toBeInTheDocument();
  });

  it('renders the dedicated 404 page for unknown routes', async () => {
    renderShell('/does-not-exist');
    expect(await screen.findByText(/۴۰۴ — صفحه پیدا نشد/)).toBeInTheDocument();
  });
});
