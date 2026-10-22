#ifndef SIMULATION_H
#define SIMULATION_H

struct SimulationResult {
    long long totalPoints;
    long long insideCircle;
    double piEstimate;
    double executionTime;
};

void setRandomSeed(unsigned int seed);
SimulationResult estimatePi(long long n);

#endif