import json, os, math
from collections import Counter

shard_dir = r'D:\HyDroMA\engine\reports\data\stage41_test_benchmark\shards'
records = []
for i in range(8):
    p = os.path.join(shard_dir, f'shard_{i:02d}', 'record_results.jsonl')
    with open(p, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

computed = [r for r in records if r.get('execution_status') == 'COMPUTED']
print('COMPUTED records:', len(computed))

def rmse(obs, pred):
    return math.sqrt(sum((o - p) ** 2 for o, p in zip(obs, pred)) / len(obs))

def mae(obs, pred):
    return sum(abs(o - p) for o, p in zip(obs, pred)) / len(obs)

def r2(obs, pred):
    mean = sum(obs) / len(obs)
    sst = sum((o - mean) ** 2 for o in obs)
    sse = sum((o - p) ** 2 for o, p in zip(obs, pred))
    return 1 - sse / sst if sst != 0 else float('nan')

def mape(obs, pred):
    vals = [abs((o - p) / o) * 100 for o, p in zip(obs, pred) if o != 0]
    return sum(vals) / len(vals) if vals else float('nan')

obs = [r['observed_yield'] for r in computed]
cal = [r['predicted_yield'] for r in computed]
base = [r['baseline_predicted_yield'] for r in computed]

print('=== CALIBRATED (epsilon=2.63) ===')
print('n:', len(obs))
print('RMSE:', rmse(obs, cal))
print('MAE:', mae(obs, cal))
print('bias:', sum(p - o for o, p in zip(obs, cal)) / len(obs))
print('R2:', r2(obs, cal))
print('MAPE:', mape(obs, cal))
print('sst:', sum((o - sum(obs)/len(obs)) ** 2 for o in obs))
print('sse:', sum((o - p) ** 2 for o, p in zip(obs, cal)))

print()
print('=== BASELINE (epsilon=2.2) ===')
print('RMSE:', rmse(obs, base))
print('MAE:', mae(obs, base))
print('bias:', sum(p - o for o, p in zip(obs, base)) / len(obs))
print('R2:', r2(obs, base))
print('MAPE:', mape(obs, base))
print('sse:', sum((o - p) ** 2 for o, p in zip(obs, base)))

# baseline reconstructed from calibrated via linearity
base_recon = [c * (2.2 / 2.63) for c in cal]
print()
print('=== BASELINE RECONSTRUCTED (linearity from calibrated) ===')
print('RMSE:', rmse(obs, base_recon))
print('R2:', r2(obs, base_recon))
print('max diff base vs recon:', max(abs(b - br) for b, br in zip(base, base_recon)))
print('all equal within 1e-12:', all(abs(b - br) < 1e-12 for b, br in zip(base, base_recon)))
