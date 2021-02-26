# %% Import libraries
from scipy import stats
from scipy.special import comb
import numpy as np
import matplotlib as plt
from matplotlib.pyplot import hist
import random
import pandas as pd

# %% Create class to display ads


class Probabilities:
    def __init__(self, n, T):
        self.n = n
        self.T = T

    def revenue(self, a):
        return a**0.5

    def click(self, a):
        return comb(self.n, a) * (0.2**a) * (0.8)**(self.n-a)


# %% Initiate given values
n = 10
T = 5
alpha = 7/10
beta = 99/100
probs = Probabilities(n, T)

# %% Calculate expected revenue


def expectedR(pi):
    return sum(np.prod([probs.click(pi[s]) * alpha + (1-probs.click(pi[s])) * beta for s in range(0, t)])
               * probs.click(pi[t]) * probs.revenue(pi[t]) for t in range(0, T))


# %% Simulate a user and calculate revenue

def getProb(i, j, pi):
    if (i == 0 or i == 14 or i == 15):
        if (j == 0):
            return 1
        else:
            return 0

    if (i % 3 == 1):
        if (j == i+1):
            return probs.click(pi[(i-1)//3])
        elif (j == i+2):
            return 1 - probs.click(pi[(i-1)//3])

    if (i % 3 == 2):
        if (j == i+2):
            return alpha
        elif (j == 0):
            return 1 - alpha

    if (i % 3 == 0):
        if (j == i+1):
            return beta
        elif (j == 0):
            return 1 - beta

    return 0


def simMarkovChain(P, nrStates):
    states = []
    states.append(1)
    while states[-1] != 0:
        nextState = random.choices(range(nrStates), weights=P[states[-1]], k=1)
        states.append(nextState[0])
    return states


def calcRevenue(states, pi):
    # Calculate revenue from states
    revenue = 0
    for state in states:
        if (state == 0):
            return revenue

        if (state % 3 == 2):
            revenue += probs.revenue(pi[(state-2)//3])


def simulationR(pi, numIter):
    # Retrieve state path with markov chain
    nrStates = 3*len(pi)+1
    P = [[getProb(i, j, pi) for j in range(nrStates)] for i in range(nrStates)]

    revenues = []
    for i in range(numIter):
        states = simMarkovChain(P, nrStates)
        revenue = calcRevenue(states, pi)
        revenues.append(revenue)

    hist(revenues, bins=[i/2 for i in range(16)])

    return np.mean(revenues)


# %% Policy 1
# The sequence of ads encountered
pi = [i for i in range(1, T+1)]

# The expected revenue calculated using the expectedR function
expRev = expectedR(pi)
print(f"Expected revenue with policy 1 for {pi}: {expRev}")

# The simulated revenue calculated using the simulation function
simRev = simulationR(pi, 100000)
print(f"Simulation revenue with policy 1 for {pi}: {simRev}")

# %% Policy 2
# Sort ads in nondecreasing order


def sortfunction(e):
    numerator = probs.click(e) * probs.revenue(e)
    denominator = 1 - probs.click(e) * alpha - (1-probs.click(e)) * beta
    return numerator/denominator


B = [i for i in range(1, n+1)]
B.sort(reverse=True, key=sortfunction)

# %% Recursively calculate r
r = [[-np.inf for i in range(T)] for j in range(n)]


def calcR(r, bIndex, t):
    if (n - bIndex >= T - t):
        bj = B[bIndex]
        if (t != T-1):
            option1 = probs.revenue(bj) * probs.click(bj) + \
                (probs.click(bj) * alpha + (1 - probs.click(bIndex))
                 * beta) * calcR(r, bIndex+1, t+1)
            option2 = calcR(r, bIndex+1, t)
            r[bj-1][t] = max(option1, option2)
        else:
            r[bj-1][t] = probs.click(bj) * probs.revenue(bj)
        return r[bj-1][t]
    return -np.inf


for t in range(T):
    calcR(r, 0, t)

# %% Calculate pi
pi = []

for t in range(T):
    maxAd = 0
    maxR = -np.inf
    for j in range(n):
        if (r[j][t] > maxR and j+1 not in pi):
            maxAd = j+1
            maxR = r[j][t]
    pi.append(maxAd)

# %% Calculate revenue
# The expected revenue calculated using the expectedR function
expRev = expectedR(pi)
print(f"Expected revenue with policy 2 for {pi}: {expRev}")

# The simulated revenue calculated using the simulation function
simRev = simulationR(pi, 100000)
print(f"Simulation revenue with policy 2 for {pi}: {simRev}")
# %%
