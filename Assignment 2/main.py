# %% imports
import pandas as pd
from collections import deque
import random
import math
import statistics
import random

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
    line.insert(0, 1-sum(line))

print(pd.DataFrame(p))

# %%
# Calculates the time between the last external arrival and the next external arrival
# (https://timeseriesreasoning.com/2019/10/12/poisson-process-simulation/)
def next_arrival(station_index):
    rate = lambdas[station_index]
    n = random.random()
    inter_event_time = -math.log(1.0 - n) / h
    return inter_event_time

# %% handle customer
def handleCustomer(customer, station): 
    # select queue to move to
    nextQueue = random.choices(range(N+1), weights=p[station-1])

    # add customer to next queue or let him leave the system
    if (nextQueue == 0):
        queues[nextQueue].put(customer)

# %%
def discipline1(stationQ, stationi):
    while not stationQ.empty():
        cust = stationQ.get()
        handleCustomer(cust, stationi) #handle custumer
        stationQ.task_done()
    #All custumer for station i has been served.
# %%
def discipline2(stationQ, stationi):
    i = 0
    while (not stationQ.empty()) and (k[stationi] < i):
        cust = stationQ.get()
        handleCustomer(cust, stationi)
        stationQ.task_done()
        i += 1
    #All custumer or up to k custumers for station i has been served.
# %%
def discipline3(stationQ, stationi):
    ki = stationQ.qsize()
    for i in range(ki):
        cust = stationQ.get()
        handleCustomer(cust, stationi)
        stationQ.task_done()
    #No new custumers are served in stationQ