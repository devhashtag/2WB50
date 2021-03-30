from scipy.stats import expon, uniform
from collections import deque
from math import sin, pi 
import matplotlib.pyplot as plt

# Simulates a non-homogenous poisson process
class NHPP:
    def __init__(self, rate_function, max_rate):
        self.rate_function = rate_function
        self.max_rate = max_rate
        self.exp_dist = expon(scale=1/max_rate)
        self.uni_dist = uniform(0, 1)

    def arrivals(self, start, end):
        arrivals = deque()
        time = start

        while True:
            time += self.exp_dist.rvs()
            if time > end:
                break

            accept = self.max_rate * self.uni_dist.rvs() < self.rate_function(time)
            if accept:
                arrivals.append(time)

        return list(arrivals)