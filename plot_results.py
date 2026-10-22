
import csv
import matplotlib.pyplot as plt

sample_sizes = []
mean_errors = []

with open("comparison.csv", "r", newline="") as file:
    reader = csv.DictReader(file)

    for row in reader:
        sample_sizes.append(int(row["samples"]))
        mean_errors.append(float(row["mean_absolute_error"]))

if not sample_sizes:
    raise ValueError("comparison.csv contains no result rows.")


# Experimental error curve
plt.figure(figsize=(9, 5))

plt.plot(
    sample_sizes,
    mean_errors,
    marker="o",
    label="Experimental mean absolute error"
)

# Theoretical reference curve, anchored at the first data point
reference_errors = [
    mean_errors[0] * (sample_sizes[0] / n) ** 0.5
    for n in sample_sizes
]

plt.plot(
    sample_sizes,
    reference_errors,
    linestyle="--",
    label="Reference: error proportional to 1/sqrt(N)"
)

plt.xscale("log")
plt.yscale("log")
plt.xlabel("Random points per trial")
plt.ylabel("Mean absolute error")
plt.title("Monte Carlo Pi: Experimental vs Theoretical Trend")
plt.grid(True, which="both", linestyle="--", alpha=0.5)
plt.legend()

plt.tight_layout()
plt.savefig("accuracy_comparison.png", dpi=150)
plt.show()
