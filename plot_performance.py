
import csv
import matplotlib.pyplot as plt

samples = []
throughput = []

with open("comparison.csv", "r", newline="") as file:
    reader = csv.DictReader(file)

    for row in reader:
        samples.append(int(row["samples"]))
        throughput.append(float(row["points_per_second"]))

if not samples:
    raise ValueError("No results found in comparison.csv.")

plt.figure(figsize=(9, 5))
plt.plot(samples, throughput, marker="o")
plt.xscale("log")
plt.xlabel("Random points per trial")
plt.ylabel("Points processed per second")
plt.title("Monte Carlo Simulation Performance")
plt.grid(True, which="both", linestyle="--", alpha=0.5)
plt.tight_layout()
plt.savefig("performance_plot.png", dpi=150)
plt.show()
