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


# %% Initiate given values
n = 10
T = 5
alpha = 7/10
beta = 99/100
probs = Probabilities(n, T)

# %% Calculate expected revenue


def expectedR(pi, beta, alpha):
    return sum(np.prod([probs.click(pi[s]) * alpha + (1-probs.click(pi[s])) * beta for s in range(0, t)])
               * probs.click(pi[t])*probs.revenue(pi[t]) for t in range(0, T))


# %% Policy 1
pi = [i for i in range(1, T+1)]
test = expectedR(pi, beta, alpha)
print(test)


# %% Policy 2

# %%
