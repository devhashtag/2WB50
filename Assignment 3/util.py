from scipy.stats import expon, uniform
from collections import deque
from math import sin, pi 
import matplotlib.pyplot as plt
import heapq

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


# copied and adapted from lecture notes
class FES:
    def __init__(self):
        self.events = []

    def enqueue(self, event):
        heapq.heappush(self.events, event)

    def pop(self):
        self.ensure_not_empty()
        return heapq.heappop(self.events)

    def peek(self):
        self.ensure_not_empty()
        return self.events[0]

    def clear(self):
        self.events = []

    def is_empty(self):
        return len(self.events) == 0

    def ensure_not_empty(self):
        if len(self.events) == 0:
            raise RuntimeError('The queue is empty')

def to_time(minutes):
    minutes = round(minutes)
    return f'{((minutes // 60) % 24):02}:{(minutes % 60):02}'