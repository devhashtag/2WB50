# %% Import libraries
from scipy import stats
from scipy.special import comb
import numpy as np
import matplotlib as plt

# %% Create class to display ads


class Probabilities:
    def __init__(self, n, T):
        self.n = n
        self.T = T

    def revenue(self, a):
        return a**0.5

    def click(self, a):
        return comb(self.n, a) * (0.2**a) * (0.8)**(self.n-a)

    def scan_next(self, a):
        return 99/100

    def scan_next_after_click(self, a):
        return 7/10


# %% Initiate given values
n = 10
T = 5
probs = Probabilities(n, T)

# %% Calculate expected revenue
def expectedR(pi, a, beta, values, prob):
    sum = prob[pi[1]]*values[pi[1]]

    for t in range(2,T+1):
        times = 1
        for s in range(2, t):
            times *= prob[pi[s]]*a[pi[s]] + (1-prob[pi[s]]*beta)
        sum += times*prob[pi[t]]*values[pi[t]]
    return sum


# %% Policy 1
pi = [i for i in range(1,11)]


# %% Policy 2

# %%
