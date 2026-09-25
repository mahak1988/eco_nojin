import type { MetadataRoute } from 'next';

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: 'HyDroMa Nojin',
    short_name: 'HyDroMa',
    description: 'Data and science for landscape restoration.',
    start_url: '/fa',
    display: 'standalone',
    background_color: '#f6f5ef',
    theme_color: '#0e1a1e',
    lang: 'fa',
    dir: 'rtl',
    icons: [
      { src: '/icon.png', sizes: '192x192', type: 'image/png' },
      { src: '/apple-icon.png', sizes: '512x512', type: 'image/png' },
    ],
  };
}
