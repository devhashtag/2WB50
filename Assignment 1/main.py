# %%
from scipy import stats
from scipy.special import comb
print('Hello, world!')

# %%
# Initiate given values
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

probs = Probabilities(10, 5)

A = [i for i in range(1, 11)]
T = []
pA = []
vA = [a**(1/2) for a in A]
alphaA = 7/10
betaA = 99/100

# %%
# Policy 1
pi = A
pi

# %%
# Policy 2
