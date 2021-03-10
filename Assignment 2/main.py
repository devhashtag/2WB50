# %% imports
import pandas as pd

# %% read input file
inputText = open("input4.txt", "r")

# read all lines
lambdas = [float(x) for x in inputText.readline().split()]
N = len(lambdas)
expectedB = [float(x) for x in inputText.readline().split()]
expectedR = [float(x) for x in inputText.readline().split()]
k = [float(x) for x in inputText.readline().split()]
p = [[float(x) for x in inputText.readline().split()] for y in range(N)]

# calculate pi0
for line in p:
    line.append(1-sum(line))

# %%
