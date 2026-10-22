
#ifndef SIMULATION_H
#define SIMULATION_H

struct SimulationResult {
    long long totalPoints;
    long long insideCircle;
    double piEstimate;
    double executionTime;
};

SimulationResult estimatePi(long long n);

#endif
