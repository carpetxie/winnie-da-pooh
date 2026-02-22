"""
Monte Carlo simulation: How much does CRPS inflate when you have fewer strikes?

Takes a known distribution (Normal), constructs piecewise-linear CDFs with
2, 3, 4, and 5 strikes at realistic spacing, computes CRPS against the same
realized outcomes, and reports the inflation.
"""
import numpy as np
from scipy import stats

def crps_piecewise_linear(strikes, cdf_values, realized):
    """Compute CRPS for a piecewise-linear CDF defined by (strikes, cdf_values).
    
    CDF = 0 below min strike, 1 above max strike, linear interpolation between.
    CRPS = integral of (F(x) - 1[x >= realized])^2 dx
    """
    # Build extended points: (-inf side, strikes, +inf side)
    # We integrate from a lower bound to an upper bound
    # For numerical purposes, extend domain
    lower = min(strikes[0], realized) - abs(realized - strikes[0]) - 10
    upper = max(strikes[-1], realized) + abs(realized - strikes[-1]) + 10
    
    # Build breakpoints
    breakpoints = sorted(set([lower, upper, realized] + list(strikes)))
    
    total = 0.0
    for i in range(len(breakpoints) - 1):
        a, b = breakpoints[i], breakpoints[i+1]
        if a >= b:
            continue
        
        # F(x) at endpoints
        def F(x):
            if x <= strikes[0]:
                return 0.0
            elif x >= strikes[-1]:
                return 1.0
            else:
                # Linear interpolation
                idx = np.searchsorted(strikes, x, side='right') - 1
                idx = max(0, min(idx, len(strikes) - 2))
                t = (x - strikes[idx]) / (strikes[idx+1] - strikes[idx])
                return cdf_values[idx] + t * (cdf_values[idx+1] - cdf_values[idx])
        
        fa, fb = F(a), F(b)
        
        # Heaviside: H(x) = 1 if x >= realized, else 0
        if b <= realized:
            # Below realized: integrand = F(x)^2
            # F is linear on [a,b]: F(x) = fa + (fb-fa)/(b-a) * (x-a)
            # integral of (fa + slope*(x-a))^2 dx from a to b
            h = b - a
            total += h * (fa**2 + fa*(fb-fa) + (fb-fa)**2/3)
        elif a >= realized:
            # Above realized: integrand = (F(x) - 1)^2
            ga, gb = fa - 1, fb - 1
            h = b - a
            total += h * (ga**2 + ga*(gb-ga) + (gb-ga)**2/3)
        else:
            # Straddles realized: split at realized
            # Below part [a, realized]
            t = (realized - a) / (b - a)
            fr = fa + t * (fb - fa)
            
            h1 = realized - a
            if h1 > 0:
                total += h1 * (fa**2 + fa*(fr-fa) + (fr-fa)**2/3)
            
            # Above part [realized, b]
            gr, gb2 = fr - 1, fb - 1
            h2 = b - realized
            if h2 > 0:
                total += h2 * (gr**2 + gr*(gb2-gr) + (gb2-gr)**2/3)
    
    return total


def run_simulation(n_trials=10000, seed=42):
    """Run Monte Carlo: known Normal distribution, varying strike counts."""
    rng = np.random.RandomState(seed)
    
    # Parameters matched to CPI-like and Jobless Claims-like distributions
    scenarios = {
        'CPI-like (σ=0.1pp)': {'mu': 0.3, 'sigma': 0.1, 'strike_range': (0.1, 0.5), 'spacing': 'uniform'},
        'Jobless Claims-like (σ=8K)': {'mu': 225, 'sigma': 8, 'strike_range': (205, 245), 'spacing': 'clustered'},
    }
    
    results = {}
    
    for scenario_name, params in scenarios.items():
        mu, sigma = params['mu'], params['sigma']
        lo, hi = params['strike_range']
        
        # Generate realized values from the true distribution
        realized_values = rng.normal(mu, sigma, n_trials)
        
        # True CRPS of N(mu, sigma) = sigma * (1/sqrt(pi) - 1/sqrt(2*pi)) ≈ sigma * 0.2821
        # But we want to measure: CRPS of piecewise-linear approximation vs truth
        
        crps_by_nstrikes = {}
        
        for n_strikes in [2, 3, 4, 5, 7, 10]:
            if params['spacing'] == 'uniform':
                strikes = np.linspace(lo, hi, n_strikes)
            else:
                # Clustered near mean (realistic for Jobless Claims)
                strikes = np.linspace(lo, hi, n_strikes)
                # Pull strikes toward mean
                strikes = mu + (strikes - mu) * 0.7  # Slight clustering
                strikes = np.sort(strikes)
            
            # True CDF values at these strikes
            cdf_values = stats.norm.cdf(strikes, mu, sigma)
            
            crps_vals = []
            for realized in realized_values:
                c = crps_piecewise_linear(strikes, cdf_values, realized)
                crps_vals.append(c)
            
            crps_by_nstrikes[n_strikes] = np.mean(crps_vals)
        
        results[scenario_name] = crps_by_nstrikes
        
        # Also compute "true" CRPS (many strikes = good approximation)
        many_strikes = np.linspace(lo - 2*sigma, hi + 2*sigma, 100)
        many_cdf = stats.norm.cdf(many_strikes, mu, sigma)
        crps_true = []
        for realized in realized_values:
            c = crps_piecewise_linear(many_strikes, many_cdf, realized)
            crps_true.append(c)
        results[scenario_name]['true_approx'] = np.mean(crps_true)
    
    # Report
    print("=" * 80)
    print("STRIKE COUNT SIMULATION: CRPS inflation from coarse CDF approximation")
    print("=" * 80)
    print(f"N trials: {n_trials}")
    print()
    
    for scenario_name, crps_dict in results.items():
        true_crps = crps_dict['true_approx']
        print(f"\n--- {scenario_name} ---")
        print(f"  True CRPS (100-strike approx): {true_crps:.6f}")
        print(f"  {'Strikes':<10} {'CRPS':<12} {'Inflation vs True':<20} {'Inflation 2→N':<20}")
        
        crps_2 = crps_dict[2]
        for n in [2, 3, 4, 5, 7, 10]:
            c = crps_dict[n]
            inflation_vs_true = (c / true_crps - 1) * 100
            inflation_vs_2 = (1 - c / crps_2) * 100  # Reduction from 2-strike
            print(f"  {n:<10} {c:<12.6f} {inflation_vs_true:>+8.1f}%            {inflation_vs_2:>+8.1f}%")
    
    # Key comparison: 2 strikes vs 3 strikes (the CPI vs Jobless Claims gap)
    print("\n" + "=" * 80)
    print("KEY RESULT: Going from 2 to 3 strikes")
    print("=" * 80)
    for scenario_name, crps_dict in results.items():
        c2, c3 = crps_dict[2], crps_dict[3]
        inflation = (c2 / c3 - 1) * 100
        print(f"  {scenario_name}: CRPS inflates by {inflation:.1f}% with 2 vs 3 strikes")
    
    print("\n  Paper finding: CPI CRPS/MAE penalty = 32% (ratio 1.32)")
    print("  If strike-count explains <10%, the finding is robust.")
    print("  If strike-count explains >20%, it's substantially a measurement artifact.")

if __name__ == '__main__':
    run_simulation()
