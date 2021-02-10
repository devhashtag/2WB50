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


# %% Policy 1
pi = A


# %% Policy 2
