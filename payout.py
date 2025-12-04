import math
import matplotlib.pyplot as plt

# Benchmark data
benchmarks = [
    (10000, 45),
    (25000, 80),
    (50000, 160),
    (100000, 260),
    (250000, 370),
    (500000, 650),
    (1000000, 850),
    (5000000, 2500),
]

def payout(views: int) -> int:
    if views <= benchmarks[0][0]:
        return benchmarks[0][1]
    if views >= benchmarks[-1][0]:
        return benchmarks[-1][1]

    for i in range(len(benchmarks)-1):
        v0, p0 = benchmarks[i]
        v1, p1 = benchmarks[i+1]
        if v0 <= views <= v1:
            log_ratio = (math.log10(views) - math.log10(v0)) / (math.log10(v1) - math.log10(v0))
            payout_value = p0 + log_ratio * (p1 - p0)
            return round(payout_value)

# Generate data for graph
view_values = list(range(1000, 5000001, 1000))  # From 1k to 5M views
payout_values = [payout(v) for v in view_values]

# Plot
plt.figure(figsize=(10,6))
plt.plot(view_values, payout_values, label="Creator Payout", color="blue")
plt.scatter([v for v,_ in benchmarks], [p for _,p in benchmarks], color="red", label="Benchmarks")
plt.xscale("log")
plt.xlabel("Views (log scale)")
plt.ylabel("Payout ($)")
plt.title("UGC Creator Payout vs Views")
plt.legend()
plt.grid(True, which="both", linestyle="--", alpha=0.5)
plt.show()
