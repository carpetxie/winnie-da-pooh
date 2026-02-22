"""Check temporal CRPS computation methods."""
import json
import numpy as np
from collections import defaultdict

with open('/Users/jeffreyxie/Desktop/winnie/data/exp13/unified_results.json') as f:
    data = json.load(f)

temporal = data['temporal_crps']

# Group by series and lifetime_pct
groups = defaultdict(lambda: {'kalshi': [], 'uniform': []})
for rec in temporal:
    key = (rec['series'], rec['lifetime_pct'])
    groups[key]['kalshi'].append(rec['kalshi_crps'])
    groups[key]['uniform'].append(rec['uniform_crps'])

print("Comparison of ratio computation methods:")
print(f"{'Series':<20} {'Pct':<6} {'Mean of ratios':<18} {'Ratio of means':<18} {'Median of ratios':<18}")
for series in ['KXCPI', 'KXJOBLESSCLAIMS']:
    for pct in ['10%', '50%', '90%']:
        k = np.array(groups[(series, pct)]['kalshi'])
        u = np.array(groups[(series, pct)]['uniform'])
        ratios = k / u
        mean_of_ratios = np.mean(ratios)
        ratio_of_means = np.mean(k) / np.mean(u)
        median_of_ratios = np.median(ratios)
        print(f"{series:<20} {pct:<6} {mean_of_ratios:<18.3f} {ratio_of_means:<18.3f} {median_of_ratios:<18.3f}")
