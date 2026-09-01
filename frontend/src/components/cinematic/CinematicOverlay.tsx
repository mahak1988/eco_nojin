import { useArtisticStore } from '../../hooks/useArtisticStore';

export function CinematicOverlay() {
  const { enableLetterbox, enableFilmGrain, enableLensFlare } = useArtisticStore();

  return (
    <>
      {/* Letterbox bars */}
      {enableLetterbox && (
        <>
          <div style={{
            position: 'absolute', top: 0, left: 0, right: 0, height: '8vh',
            background: '#000', zIndex: 500, pointerEvents: 'none',
          }} />
          <div style={{
            position: 'absolute', bottom: 0, left: 0, right: 0, height: '8vh',
            background: '#000', zIndex: 500, pointerEvents: 'none',
          }} />
        </>
      )}

      {/* Film grain */}
      {enableFilmGrain && (
        <div style={{
          position: 'absolute', inset: 0, zIndex: 501, pointerEvents: 'none',
          opacity: 0.08,
          backgroundImage: 'url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")',
        }} />
      )}

      {/* Lens flare */}
      {enableLensFlare && (
        <div style={{
          position: 'absolute', top: '20%', left: '70%', width: '150px', height: '150px',
          background: 'radial-gradient(circle, rgba(255,248,220,0.4) 0%, transparent 70%)',
          borderRadius: '50%', zIndex: 502, pointerEvents: 'none',
          filter: 'blur(2px)',
        }} />
      )}
    </>
  );
}
