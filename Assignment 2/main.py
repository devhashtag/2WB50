# %% imports
import pandas as pd
import random
import math
import statistics
import random
import numpy as np
from scipy import stats
from numpy import array, dot
from numpy.linalg import LinAlgError
from queue import Queue

inputText = '''0.02	0.03	0.02	0.03	0.07	0.01
1.	0.4	0.5	0.8	0.9	0.8
1.2	2.	1.8	1.8	0.2	1.2
4.	5.	4.	5.	6.	4.
0.1	0.15	0.15	0.15	0.13	0.1
0.11	0.16	0.16	0.11	0.16	0.16
0.16	0.16	0.11	0.13	0.13	0.11
0.12	0.15	0.1	0.15	0.15	0.12
0.13	0.15	0.1	0.13	0.13	0.1
0.15	0.15	0.1	0.15	0.1	0.12
'''
text_lines = inputText.split('\n')
text_lines.reverse()

class OutOfTimeError(Exception):
    pass

# %% define customer class
class Customer:    
    next_id = 1

    def __init__(self, time):
        self.arrivalTime = time
        self.id = Customer.next_id
        Customer.next_id += 1
  
    def getTotalTime(self, time):
        return time - self.arrivalTime

    def setWaitingTime(self, time):
        self.waitingTime = time    

    def getWaitingTime(self, time):
        return round(time - self.waitingTime, 1)

    def __str__(self):
        return f'Id: {self.id}'

    def __repr__(self):
        return self.__str__()

# %% read input file
# inputText = open('input4.txt', 'r')

# read all lines
lambdas = [float(x) for x in text_lines.pop().split()]
N = len(lambdas)
expectedB = [float(x) for x in text_lines.pop().split()]
expectedR = [float(x) for x in text_lines.pop().split()]
k = [float(x) for x in text_lines.pop().split()]
p = [[float(x) for x in text_lines.pop().split()] for y in range(N)]

duration = 1000

# calculate pi0
for line in p:
    line.insert(0, 1-sum(line))
print(pd.DataFrame(p))

service_rvs = []

for i in range(N):
    service_rvs.append(stats.expon(scale=expectedB[i]))

def sample_service_time(station_index):
    return service_rvs[station_index].rvs(1)[0]

# %%
'''
Calculates the total (external + internal) arrival rate of customers for each queue
'''
def calc_arrival_rate():
    # set up the equations as matrices
    p_ = array(p)
    coefficients = np.delete(p_, 0, 1).T - np.identity(N)
    solutions = -1 * array(lambdas).reshape((N, 1))
    try:
        gammas = np.linalg.inv(coefficients) @ solutions
        return gammas.flatten()
    except LinAlgError:
        raise Exception('Infinite amount of solutions possible for the theorical total arrival rates. This usually only happens if there is a station with a self-loop of probability 1.')

'''
Calculates the total network utilisation.
The system is stable if this value is strictly less than 1,
otherwise all performance measures will be infinite
'''
def calc_network_utilisation():
    gammas = calc_arrival_rate()
    service_times = expectedB
    return dot(gammas, service_times)

'''
Calculates the expected cycle time of the rover.
More precise: it is the mean time between two consecutive arrivals
of the rover at station i.
'''
def calc_expected_cycle_time():
    r = sum(expectedR)
    rho = calc_network_utilisation()
    return r / (1 - rho)

# %%
# Calculates the time between the last external arrival and the next external arrival
# (https://timeseriesreasoning.com/2019/10/12/poisson-process-simulation/)
def calc_next_arrival(rover_station):
    rate = lambdas[rover_station]
    n = random.random()
    inter_event_time = -math.log(1.0 - n) / rate 
    return inter_event_time


# %% handle customer
def handleCustomer(queues, customer, rover_station, time): 
    # select queue to move to
    nextQueue = random.choices(range(N+1), weights=p[rover_station])

    # add customer to next queue or let him leave the system
    if (nextQueue[0] != 0):
        print(f'nextQueue {nextQueue[0]}')
        customer.setWaitingTime(time)
        queues[nextQueue[0]-1].put(customer)
    else:
        print(f'{customer} left the system')

# %%
def discipline1(queues, rover_station, next_arrivals, time):
    stationQ = queues[rover_station]
    while not stationQ.empty():
        # print_q(stationQ)
        cust = stationQ.get()
        handleCustomer(queues, cust, rover_station, time) #handle custumer
        time += sample_service_time(rover_station)
        stationQ.task_done()
        # print_q(stationQ)
        check_time(queues, next_arrivals, time)

    #All custumer for station i has been served.
    return time

# %%
def discipline2(queues, rover_station, next_arrivals, time):
    stationQ = queues[rover_station]
    i = 0
    while (not stationQ.empty()) and (i < k[rover_station]):
        cust = stationQ.get()
        handleCustomer(queues, cust, rover_station, time)
        time += sample_service_time(rover_station)
        stationQ.task_done()
        i += 1
        check_time(queues, next_arrivals, time)

    #All custumer or up to k custumers for station i has been served.
    return time

# %%
def discipline3(queues, rover_station, next_arrivals, time):
    stationQ = queues[rover_station]
    ki = stationQ.qsize()
    for i in range(ki):
        cust = stationQ.get()
        handleCustomer(queues, cust, rover_station, time)
        time += sample_service_time(rover_station)
        stationQ.task_done()
        check_time(queues, next_arrivals, time)

    #No new custumers are served in stationQ
    return time

# %%
def nextStation(rover_position, time):
    time += expectedR[rover_position]
    rover_position = (rover_position + 1) % N
    return rover_position, time

# %%
def check_time(queues, next_arrivals, current_time):
    # print(current_time)
    check_arrivals(queues, next_arrivals, current_time)
    if current_time >= duration:
        raise OutOfTimeError()

def check_arrivals(queues, next_arrivals, time):
    for i in range(N):
        arrival_time = next_arrivals[i]
        if (arrival_time <= time):
            next_arrivals[i] += calc_next_arrival(i)
            queue = queues[i]
            customer = Customer(arrival_time)
            customer.setWaitingTime(time)
            queue.put(customer)
            print(f'{customer} entered the system')
         
def print_q(index, queue, time):
    print(f"Queue {index+1}: ", end='')
    print([cust.getWaitingTime(time) for cust in list(queue.queue)])

def simulation(discipline):
    random.seed(42)
    # initialize queues
    queues = [Queue() for _ in range(N)]
    
    # start time at 0 and rover at station 1
    time = 0.0
    rover_station = 0
    next_arrivals = [calc_next_arrival(i) for i in range(N)]

    try:
        while True:
            print(f"Current station: {rover_station+1}")
            time = discipline(queues, rover_station, next_arrivals, time)
            rover_station, time = nextStation(rover_station, time)
            check_time(queues, next_arrivals, time)
            [print_q(index, queues[index], time) for index in range(len(queues))]
    except OutOfTimeError:
        print("Out of time")
        pass
    finally:
        pass
        # give output
        
# %%
simulation(discipline2)