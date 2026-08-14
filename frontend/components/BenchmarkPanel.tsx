'use client';
import { useState } from 'react';
import { useI18n } from '../lib/i18n-context';
import { API_BASE } from '../lib/config';

export default function BenchmarkPanel() {
  const { t } = useI18n();
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [arraySize, setArraySize] = useState(1000);
  const [iterations, setIterations] = useState(5);

  const runBenchmark = async () => {
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/api/v1/benchmark/ndvi`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          array_size: arraySize,
          iterations: iterations,
        }),
      });

      if (!res.ok) throw new Error('Benchmark failed');
      setResult(await res.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const speedupColor = result?.speedup >= 5 ? '#16a34a' : result?.speedup >= 2 ? '#f59e0b' : '#dc2626';

  return (
    <section
      aria-labelledby="benchmark-panel-title"
      style={{
        marginTop: '32px',
        padding: '24px',
        border: '1px solid #ddd',
        borderRadius: '12px',
        background: '#f3e8ff',
      }}
    >
      <h2 id="benchmark-panel-title" style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '16px', color: '#6b21a8' }}>
        ⚡ {t('benchmark_title')}
      </h2>

      <div style={{ display: 'flex', gap: '12px', marginBottom: '16px', flexWrap: 'wrap', alignItems: 'flex-end' }}>
        <div>
          <label htmlFor="bench-size" style={{ display: 'block', fontSize: '0.875rem', marginBottom: '4px' }}>{t('array_size')}</label>
          <input
            id="bench-size"
            type="number"
            value={arraySize}
            onChange={(e) => setArraySize(parseInt(e.target.value))}
            style={{ padding: '8px', border: '1px solid #ccc', borderRadius: '6px', width: '120px' }}
          />
        </div>

        <div>
          <label htmlFor="bench-iter" style={{ display: 'block', fontSize: '0.875rem', marginBottom: '4px' }}>{t('iterations')}</label>
          <input
            id="bench-iter"
            type="number"
            value={iterations}
            onChange={(e) => setIterations(parseInt(e.target.value))}
            style={{ padding: '8px', border: '1px solid #ccc', borderRadius: '6px', width: '120px' }}
          />
        </div>

        <button
          onClick={runBenchmark}
          disabled={loading}
          aria-busy={loading}
          style={{ padding: '10px 24px', background: '#6b21a8', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' }}
        >
          {loading ? t('analyzing') : t('run_benchmark')}
        </button>
      </div>

      {error && <p role="alert" style={{ color: '#dc2626' }}>{t('error_label')}: {error}</p>}

      {result && (
        <div aria-live="polite" style={{ background: 'white', padding: '16px', borderRadius: '8px', marginTop: '16px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: '600', marginBottom: '12px' }}>
            NDVI {t('benchmark_title')} ({result.array_size}×{result.array_size})
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '12px' }}>
            <div style={{ padding: '12px', background: '#fef2f2', borderRadius: '6px', textAlign: 'center' }}>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#dc2626' }}>
                {result.numpy_time_ms.toFixed(2)}
              </div>
              <div style={{ fontSize: '0.875rem', color: '#4b5563' }}>{t('numpy_time')} (ms)</div>
            </div>

            <div style={{ padding: '12px', background: '#ecfdf5', borderRadius: '6px', textAlign: 'center' }}>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#16a34a' }}>
                {result.numba_time_ms.toFixed(2)}
              </div>
              <div style={{ fontSize: '0.875rem', color: '#4b5563' }}>{t('numba_time')} (ms)</div>
            </div>

            <div style={{ padding: '12px', background: '#f0fdf4', borderRadius: '6px', textAlign: 'center', border: '2px solid #16a34a' }}>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: speedupColor }}>
                {result.speedup.toFixed(1)}x
              </div>
              <div style={{ fontSize: '0.875rem', color: '#4b5563' }}>{t('speedup')}</div>
            </div>
          </div>

          {/* Visual comparison bar */}
          <div style={{ marginTop: '16px' }}>
            <div style={{ marginBottom: '8px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem', marginBottom: '4px' }}>
                <span>NumPy</span>
                <span>{result.numpy_time_ms.toFixed(2)} ms</span>
              </div>
              <div style={{ height: '24px', background: '#fee2e2', borderRadius: '4px', overflow: 'hidden' }}>
                <div style={{ width: '100%', height: '100%', background: '#dc2626' }} />
              </div>
            </div>

            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem', marginBottom: '4px' }}>
                <span>Numba</span>
                <span>{result.numba_time_ms.toFixed(2)} ms</span>
              </div>
              <div style={{ height: '24px', background: '#dcfce7', borderRadius: '4px', overflow: 'hidden' }}>
                <div style={{
                  width: `${(result.numba_time_ms / result.numpy_time_ms) * 100}%`,
                  height: '100%',
                  background: '#16a34a'
                }} />
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
