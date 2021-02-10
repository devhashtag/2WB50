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

    def scan_next(self):
        return 99/100

    def scan_next_after_click(self):
        return 7/10


# %% Initiate given values
n = 10
T = 5
probs = Probabilities(n, T)

# %% Calculate expected revenue
def expectedR(pi, a, beta, values, probA, alpha):
    sumR = 0
    for t in range(0,T):
        times = 1
        for s in range(0, t):
            times = times * (probA[pi[s]] * alpha + (1-probA[pi[s]]*beta))
            print(times)
        sumR += times*probA[pi[t]]*values[pi[t]]
    
    return sumR


# %% Policy 1
pi = [i for i in range(1, T+1)]
probPerA = [probs.click(i) for i in range(1,n)]
revPerA = [probs.revenue(i) for i in range(1,n)]
test = expectedR(pi, pi, probs.scan_next(), revPerA, probPerA, probs.scan_next_after_click())
print(test)


# %% Policy 2

# %%

# %%
