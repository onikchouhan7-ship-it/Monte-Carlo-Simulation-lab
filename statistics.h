
#ifndef STATISTICS_H
#define STATISTICS_H

struct Statistics {
    double meanEstimate;
    double meanAbsoluteError;
    double averageTime;
    double pointsPerSecond;
};

Statistics calculateStats(
    double sumEstimates,
    double sumAbsoluteErrors,
    double sumTime,
    int trials,
    long long n
);

#endif
