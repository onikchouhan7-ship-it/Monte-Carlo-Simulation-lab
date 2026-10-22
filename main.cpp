
#include <iostream>
#include <fstream>
#include <random>
#include <iomanip>
#include <chrono>
#include "simulation.h"
#include "statistics.h"

using namespace std;
using namespace chrono;

int main() {
    int trials;
    long long startN;
    unsigned int seed;

    cout << "Enter random seed: ";
    if (!(cin >> seed)) {
        cerr << "Invalid seed.\n";
        return 1;
    }

    setRandomSeed(seed);

    cout << "==============================\n";
    cout << "   MONTE CARLO SIMULATION LAB\n";
    cout << "==============================\n";

    cout << "Enter number of trials: ";
    if (!(cin >> trials) || trials <= 0 || trials > 10000) {
        cerr << "Enter trials between 1 and 10000.\n";
        return 1;
    }

    cout << "Enter starting sample size: ";
    if (!(cin >> startN) || startN <= 0 ||
        startN > 1000000LL) {
        cerr << "Enter a starting sample size between 1 and 1000000.\n";
        return 1;
    }

    const double actualPi = 3.14159265358979323846;

    ofstream file("comparison.csv");

    if (!file.is_open()) {
        cerr << "Error opening comparison.csv\n";
        return 1;
    }

    file << "samples,trials,mean_estimate,mean_absolute_error,"
         << "average_time,points_per_second\n";

    cout << fixed << setprecision(8);
    file << fixed << setprecision(8);

    cout << "\n========== COMPARISON ==========\n";

    for (int level = 0; level < 4; level++) {
        long long n = startN;

        for (int k = 0; k < level; k++) {
            n *= 10;
        }

        double sumEstimates = 0.0;
        double sumAbsoluteErrors = 0.0;
        double sumTime = 0.0;

        for (int i = 0; i < trials; i++) {
            SimulationResult result = estimatePi(n);

            double error = result.piEstimate - actualPi;

            if (error < 0.0) {
                error = -error;
            }

            sumEstimates += result.piEstimate;
            sumAbsoluteErrors += error;
            sumTime += result.executionTime;
        }

        // Calculate all summary statistics using our function.
        Statistics stats = calculateStats(
            sumEstimates,
            sumAbsoluteErrors,
            sumTime,
            trials,
            n
        );

        cout << "\nSample size: " << n << '\n';
        cout << "Trials: " << trials << '\n';
        cout << "Mean estimate: "
             << stats.meanEstimate << '\n';
        cout << "Mean absolute error: "
             << stats.meanAbsoluteError << '\n';
        cout << "Average time: "
             << stats.averageTime << " seconds\n";
        cout << "Throughput: "
             << stats.pointsPerSecond
             << " points/second\n";

        file << n << ','
             << trials << ','
             << stats.meanEstimate << ','
             << stats.meanAbsoluteError << ','
             << stats.averageTime << ','
             << stats.pointsPerSecond << '\n';
    }

    file.close();

    cout << "\nResults saved to comparison.csv\n";

    return 0;
}
