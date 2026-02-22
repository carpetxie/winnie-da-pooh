"""Bootstrap CIs for temporal CRPS evolution ratios."""
import json
import numpy as np

with open('/Users/jeffreyxie/Desktop/winnie/data/exp13/unified_results.json') as f:
    data = json.load(f)

temporal = data['temporal_crps']

# Group by series and lifetime_pct
from collections import defaultdict
groups = defaultdict(list)
for rec in temporal:
    key = (rec['series'], rec['lifetime_pct'])
    ratio = rec['kalshi_crps'] / rec['uniform_crps'] if rec['uniform_crps'] > 0 else np.nan
    groups[key].append(ratio)

rng = np.random.RandomState(42)
B = 10000

print("Temporal CRPS/Uniform ratios with 95% bootstrap CIs")
print("=" * 80)

for series in ['KXCPI', 'KXJOBLESSCLAIMS']:
    print(f"\n--- {series} ---")
    print(f"  {'Lifetime':<12} {'Mean Ratio':<14} {'95% CI':<20} {'n':<5}")
    for pct in ['10%', '50%', '90%']:
        ratios = np.array(groups[(series, pct)])
        n = len(ratios)
        mean_ratio = np.mean(ratios)
        
        # Bootstrap
        boot_means = []
        for _ in range(B):
            sample = rng.choice(ratios, size=n, replace=True)
            boot_means.append(np.mean(sample))
        boot_means = np.array(boot_means)
        ci_lo = np.percentile(boot_means, 2.5)
        ci_hi = np.percentile(boot_means, 97.5)
        
        print(f"  {pct:<12} {mean_ratio:<14.2f} [{ci_lo:.2f}, {ci_hi:.2f}]       {n}")

