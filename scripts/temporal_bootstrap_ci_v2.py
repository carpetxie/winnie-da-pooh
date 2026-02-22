"""Bootstrap CIs for temporal CRPS evolution - ratio of means method."""
import json
import numpy as np
from collections import defaultdict

with open('/Users/jeffreyxie/Desktop/winnie/data/exp13/unified_results.json') as f:
    data = json.load(f)

temporal = data['temporal_crps']

groups = defaultdict(lambda: {'kalshi': [], 'uniform': []})
for rec in temporal:
    key = (rec['series'], rec['lifetime_pct'])
    groups[key]['kalshi'].append(rec['kalshi_crps'])
    groups[key]['uniform'].append(rec['uniform_crps'])

rng = np.random.RandomState(42)
B = 10000

print("Temporal CRPS/Uniform ratios (ratio-of-means) with 95% bootstrap CIs")
print("=" * 80)

for series in ['KXCPI', 'KXJOBLESSCLAIMS']:
    print(f"\n--- {series} ---")
    print(f"  {'Lifetime':<12} {'Ratio':<10} {'95% CI':<22} {'n':<5} {'CI excludes 1?'}")
    for pct in ['10%', '50%', '90%']:
        k = np.array(groups[(series, pct)]['kalshi'])
        u = np.array(groups[(series, pct)]['uniform'])
        n = len(k)
        ratio = np.mean(k) / np.mean(u)
        
        boot_ratios = []
        for _ in range(B):
            idx = rng.choice(n, size=n, replace=True)
            boot_ratios.append(np.mean(k[idx]) / np.mean(u[idx]))
        ci_lo = np.percentile(boot_ratios, 2.5)
        ci_hi = np.percentile(boot_ratios, 97.5)
        
        excludes_1 = "Yes" if ci_lo > 1 or ci_hi < 1 else "No"
        print(f"  {pct:<12} {ratio:<10.2f} [{ci_lo:.2f}, {ci_hi:.2f}]         {n:<5} {excludes_1}")

