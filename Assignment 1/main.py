# %% Import libraries
from scipy import stats
from scipy.special import comb
import numpy as np
import matplotlib as plt
import random

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


def expectedR(pi, beta, alpha):
    return sum(np.prod([probs.click(pi[s]) * alpha + (1-probs.click(pi[s])) * beta for s in range(0, t)])
               * probs.click(pi[t]) * probs.revenue(pi[t]) for t in range(0, T))


# %% Simulate a user and calculate revenue

def getProb(i, j):
    if (i == 0 or i == 14 or i == 15):
        if (j == 0):
            return 1
        else:
            return 0

    if (i % 3 == 1):
        if (j == i+1):
            return probs.click((i-1)/3)
        elif (j == i+2):
            return 1 - probs.click((i-1)/3)

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


def simMarkovChain(pi, beta, alpha):
    nrStates = 3*len(pi)+1

    P = [[getProb(i, j) for j in range(nrStates)] for i in range(nrStates)]
    print(np.matrix(P))

    states = []
    states.append(1)
    while states[-1] != 0:
        nextState = random.choices(range(nrStates), weights=p[states[-1]], k=1)
        states.append(nextState[0])
    return states


def simulationR(pi, beta, alpha):
    # Retrieve state path with markov chain
    states = simMarkovChain(pi, beta, alpha)
    print(states)
    states = [1, 3, 4, 5, 7, 8, 10, 12, 13, 15, -1]

    # Calculate revenue from states
    revenue = 0
    for state in states:
        if (state == -1):
            return revenue

        if (state % 3 == 2):
            revenue += probs.revenue((state+1)/3)


# %% Policy 1
# The sequence of ads encountered
pi = [i for i in range(1, T+1)]

# The expected revenue calculated using the expectedR function
expRev = expectedR(pi, beta, alpha)
print(f"Expected revenue: {expRev}")

# The simulated revenue calculated using the simulation function
simRev = simulationR(pi, beta, alpha)
print(f"Simulation revenue: {simRev}")

# %% Policy 2

# %%
