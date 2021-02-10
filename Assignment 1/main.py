# %% Import libraries
from scipy import stats
from scipy.special import comb
import numpy as np
import matplotlib as plt

# %% Initiate given values
n = 10
A = [i for i in range(1, n+1)]
T = []
pA = [comb(n, a) * (0.2**a) * (0.8)**(n-a) for a in A]
print(pA)
vA = [a**(1/2) for a in A]
alphaA = 7/10
betaA = 99/100

# %% Calculate expected revenue


# %% Policy 1
pi = A


# %% Policy 2
