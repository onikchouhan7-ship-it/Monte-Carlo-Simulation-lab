
#include "simulation.h"
#include <random>
#include <chrono>

using namespace std;
using namespace chrono;

SimulationResult estimatePi(long long n) {
    static mt19937 generator(random_device{}());
    uniform_real_distribution<double> distribution(-1.0, 1.0);
    if (n <= 0) return {n, 0, 0.0, 0.0};
    long long insideCircle = 0;

    auto start = steady_clock::now();

    for (long long i = 0; i < n; i++) {
        double x = distribution(generator);
        double y = distribution(generator);

        if (x * x + y * y <= 1.0) {
            insideCircle++;
        }
    }

    auto finish = steady_clock::now();

    double elapsed =
        duration<double>(finish - start).count();

    double estimate = 4.0 * insideCircle / n;

    return {n, insideCircle, estimate, elapsed};
}
