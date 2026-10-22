
#include "statistics.h"

Statistics calculateStats(
    double sumEstimates,
    double sumAbsoluteErrors,
    double sumTime,
    int trials,
    long long n
) {
    Statistics stats;

    stats.meanEstimate = sumEstimates / trials;
    stats.meanAbsoluteError = sumAbsoluteErrors / trials;
    stats.averageTime = sumTime / trials;

    stats.pointsPerSecond = (stats.averageTime > 0.0)
        ? static_cast<double>(n) / stats.averageTime
        : 0.0;

    return stats;
}
