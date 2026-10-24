import json, os, sys
from collections import Counter

shard_dir = r'D:\HyDroMA\engine\reports\data\stage41_test_benchmark\shards'
all_records = []
per_shard = {}
for i in range(8):
    p = os.path.join(shard_dir, f'shard_{i:02d}', 'record_results.jsonl')
    recs = []
    with open(p, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                recs.append(json.loads(line))
    per_shard[f'shard_{i:02d}'] = recs
    all_records.extend(recs)
    print(f'shard_{i:02d}: {len(recs)} records')

print('TOTAL across shards:', len(all_records))
status_counts = Counter(r.get('execution_status') for r in all_records)
print('Status counts:', dict(status_counts))

ids = [r.get('record_id') for r in all_records]
print('Unique record_ids:', len(set(ids)))
print('Duplicate record_ids:', len(ids) - len(set(ids)))

failed = [r for r in all_records if r.get('execution_status') == 'FAILED']
print('FAILED count:', len(failed))
for r in failed:
    print('  FAIL', r.get('record_id'), r.get('district_id'), r.get('season'), '| reason:', r.get('failure_reason'), '| mode:', r.get('computation_mode'), '| input_quality:', r.get('input_quality_status'))

blocked = [r for r in all_records if r.get('execution_status') == 'BLOCKED']
print('BLOCKED count:', len(blocked))
for r in blocked:
    print('  BLOCK', r.get('record_id'), '| reason:', r.get('failure_reason'), '| mode:', r.get('computation_mode'))

partial = [r for r in all_records if r.get('execution_status') == 'PARTIAL_INPUTS']
print('PARTIAL_INPUTS count:', len(partial))
for r in partial:
    print('  PARTIAL', r.get('record_id'), '| reason:', r.get('failure_reason'))

# Present record ids
present_ids = set(ids)
print('Present unique ids:', len(present_ids))

# Load manifest frame record ids (the full 1722 frame)
manifest = json.load(open(r'D:\HyDroMA\engine\reports\data\stage40_test_sample.json'))
sample_ids = set(manifest['record_ids'])
print('Manifest sample record_ids:', len(sample_ids))
print('frame.record_count:', manifest['frame']['record_count'])
print('selected_total:', manifest['selected_total'])

# Which sample ids are present/missing in shards
present_sample = sample_ids & present_ids
missing_sample = sample_ids - present_ids
print('Sample ids present in shards:', len(present_sample))
print('Sample ids MISSING from shards:', len(missing_sample))
print('Missing sample ids:', sorted(missing_sample, key=int)[:50])

# Check for ids in shards not in sample (extra)
extra = present_ids - sample_ids
print('Shard ids NOT in sample:', len(extra), sorted(extra, key=int)[:20])

PYEOF
