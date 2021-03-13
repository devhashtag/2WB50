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

# %% get input values


# read all lines
lambdas = [float(x) for x in text_lines.pop().split()]
N = len(lambdas)
expectedB = [float(x) for x in text_lines.pop().split()]
expectedR = [float(x) for x in text_lines.pop().split()]
k = [float(x) for x in text_lines.pop().split()]
p = [[float(x) for x in text_lines.pop().split()] for y in range(N)]

# calculate pi0
for line in p:
    line.insert(0, 1-sum(line))
print(pd.DataFrame(p))

# calculate exponential distributions for handling times
service_rvs = []

for i in range(N):
    service_rvs.append(stats.expon(scale=expectedB[i]))


def sample_service_time(station_index):
    return service_rvs[station_index].rvs(1)[0]


# %% define error class
class OutOfTimeError(Exception):
    pass

# %% define simulation class
class Simulation:

    def __init__(self, n_stations, discipline, duration, rover_station=0, seed=42):
        self.rover_station = rover_station
        self.discipline = discipline
        self.duration = duration
        self.stations = [Station(i) for i in range(n_stations)]
        self.time = 0.0
        random.seed(42)

    def getStation(self, rover_station):
        return self.stations[rover_station]

    def showResults(self):
        mean_waiting_times = [station.results.getMeanWaitingTime() for station in self.stations]
        var_waiting_times = [station.results.getVarianceWaitingTime() for station in self.stations]
        mean_queue_lengths = [station.results.getMeanQueueLength() for station in self.stations]
        var_queue_lengths = [station.results.getVarianceQueueLength() for station in self.stations]
        mean_sojourn_times = [station.results.getMeanSojournTime() for station in self.stations]
        var_sojourn_times = [station.results.getVarianceSojournTime() for station in self.stations]
        [station.results.calculateCycleTimes() for station in self.stations]
        mean_cycle_times = [station.results.getMeanCycleTime() for station in self.stations]
        var_cycle_times = [station.results.getVarianceCycleTime() for station in self.stations]
        data = {
            'E[W]': mean_waiting_times, 
            'V[W]': var_waiting_times, 
            'E[Q]': mean_queue_lengths, 
            'V[Q]': var_queue_lengths,
            'E[T]': mean_sojourn_times,
            'V[T]': var_sojourn_times,
            'E[C]': mean_cycle_times,
            'V[C]': var_cycle_times
            }
        df = pd.DataFrame(data)
        return df

    def printQueues(self):
        [station.printQueue(self.time) for station in self.stations]

    def handleQueue(self):
        queue = self.stations[self.rover_station].queue
        initialQSize = queue.qsize()
        i = 0
        while self.discipline(queue, i, initialQSize, k[self.rover_station]):
            customer = queue.get()
            self.handleCustomer(customer)
            self.time += sample_service_time(self.rover_station)
            queue.task_done()
            self.checkTime()
            i += 1

    def handleCustomer(self, customer):
        # save waiting time
        self.stations[self.rover_station].results.registerWaitingTime(customer.getWaitingTime(self.time), self.time)

        # select queue to move to
        nextQueue = random.choices(range(N+1), weights=p[self.rover_station])
        nextStation = nextQueue[0]-1

        # add customer to next queue or let him leave the system
        if (nextStation != -1):
            self.stations[nextStation].addCustomer(customer, self.time)
        else:
            self.stations[self.rover_station].handleExit(customer, self.time)

    def nextStation(self):
        self.time += expectedR[self.rover_station]
        self.stations[self.rover_station].results.registerCycleTime(self.time)
        self.rover_station = (self.rover_station + 1) % N
        self.checkTime()

    def checkTime(self):
        # save queue length
        [station.saveQueueLength(self.time) for station in self.stations]

        # check for arrivals
        [station.checkArrival(self.time) for station in self.stations]

        # stop if duration has been reached
        if self.time >= self.duration:
            raise OutOfTimeError()

    def run(self):
        try:
            while True:
                self.handleQueue()
                self.nextStation()
        except OutOfTimeError:
            print("Out of time")
            pass
        finally:
            return self.showResults()
            pass

# %% define station class
class Station:

    def __init__(self, position):
        self.position = position
        self.queue = Queue()
        self.next_arrival = 0.0
        self.calcNextArrival()
        self.results = StationResults()

    def checkArrival(self, time):
        if (self.next_arrival <= time):
            customer = Customer(self.next_arrival)
            self.queue.put(customer)
            self.calcNextArrival()

    def calcNextArrival(self):
        rate = lambdas[self.position]
        n = random.random()
        inter_event_time = -math.log(1.0 - n) / rate
        self.next_arrival += inter_event_time

    def addCustomer(self, customer, time):
        customer.setWaitingTime(time)
        self.queue.put(customer)

    def handleExit(self, customer, time):
        self.results.registerSojournTime(customer.getTotalTime(time), time)

    def saveQueueLength(self, time):
        self.results.registerQueueLength(self.queue.qsize(), time)

    def printQueue(self, time):
        print(f"Queue {self.position+1}: ", end='')
        print([cust for cust in list(self.queue.queue)])

# %% define station results class
class StationResults:

    STEADY_STATE_BOUNDARY = 1000

    def __init__(self):
        self.waiting_times = []
        self.queue_lengths = []
        self.sojourn_times = []
        self.cycle_points = []
        self.cycle_times = []

    def registerWaitingTime(self, waiting_time, time):
        if time > self.STEADY_STATE_BOUNDARY:
            self.waiting_times.append(waiting_time)

    def registerQueueLength(self, queue_length, time):
        if time > self.STEADY_STATE_BOUNDARY:
            self.queue_lengths.append(queue_length)

    def registerSojournTime(self, sojourn_time, time):
        if time > self.STEADY_STATE_BOUNDARY:
            self.sojourn_times.append(sojourn_time)

    def registerCycleTime(self, time):
        if time > self.STEADY_STATE_BOUNDARY:
            self.cycle_points.append(time)

    def calculateCycleTimes(self):
        self.cycle_times = np.diff(self.cycle_points)

    def getMeanWaitingTime(self):
        return np.mean(self.waiting_times)

    def getVarianceWaitingTime(self):
        return np.var(self.waiting_times)

    def getMeanQueueLength(self):
        return np.mean(self.queue_lengths)

    def getVarianceQueueLength(self):
        return np.var(self.queue_lengths)

    def getMeanSojournTime(self):
        return np.mean(self.sojourn_times)

    def getVarianceSojournTime(self):
        return np.var(self.sojourn_times)

    def getMeanCycleTime(self):
        return np.mean(self.cycle_times)

    def getVarianceCycleTime(self):
        return np.var(self.cycle_times)

# %% define customer class
class Customer:
    next_id = 1

    def __init__(self, time):
        self.arrival_time = time
        self.waiting_time = time
        self.id = Customer.next_id
        Customer.next_id += 1

    def getTotalTime(self, time):
        return time - self.arrival_time

    def setWaitingTime(self, time):
        self.waiting_time = time

    def getWaitingTime(self, time):
        return round(time - self.waiting_time, 1)

    def __str__(self):
        return f'Id: {self.id}'

    def __repr__(self):
        return self.__str__()

# %% define confidence interval class
class ConfidenceInterval:
    
    def __init__(self, n_stations, discipline, duration, iterations):
        self.n_stations = n_stations
        self.discipline = discipline
        self.duration = duration
        self.iterations = iterations
        self.mean_waiting_times = [[] for _ in range(n_stations)]

    def calculate(self):
        # run simulations
        for i in range(self.iterations):
            print(f"Run {i}")
            sim = Simulation(self.n_stations, self.discipline, self.duration)
            res = sim.run()
            [self.mean_waiting_times[j].append(res['E[W]'][j]) for j in range(self.n_stations)]
        
        # calculate confidence intervals of results
        self.intervals = [stats.t.interval(0.95, len(means)-1, loc=np.mean(means), scale=stats.sem(means)) for means in self.mean_waiting_times]

    def printResults(self, file):
        with open(file, "w") as text_file:
            print(f"Mean waiting times: \n{self.mean_waiting_times}\n", file=text_file)
            print(f"Intervals: ", file=text_file)
            [print(f"{interval}", file=text_file) for interval in self.intervals]
        [print(interval) for interval in self.intervals]

# %% Theoretical values

# Calculates the total (external + internal) arrival rate of customers for each queue
def calcArrivalRate():
    # set up the equations as matrices
    p_ = array(p)
    coefficients = np.delete(p_, 0, 1).T - np.identity(N)
    solutions = -1 * array(lambdas).reshape((N, 1))
    try:
        gammas = np.linalg.inv(coefficients) @ solutions
        return gammas.flatten()
    except LinAlgError:
        raise Exception(
            'Infinite amount of solutions possible for the theorical total arrival rates. This usually only happens if there is a station with a self-loop of probability 1.')


# Calculates the total network utilisation.
# The system is stable if this value is strictly less than 1,
# otherwise all performance measures will be infinite
def calcNetworkUtilisation():
    gammas = calcArrivalRate()
    service_times = expectedB
    return dot(gammas, service_times)


# Calculates the expected cycle time of the rover.
# More precise: it is the mean time between two consecutive arrivals
# of the rover at station i.
def calcExpectedCycleTime():
    r = sum(expectedR)
    rho = calcNetworkUtilisation()
    return r / (1 - rho)

# %%


def discipline1(stationQ, i, initialQSize, k):
    return not stationQ.empty()


def discipline2(stationQ, i, initialQSize, k):
    return not stationQ.empty() and i < k


def discipline3(stationQ, i, initialQSize, k):
    return not stationQ.empty() and i < initialQSize

# %% run simulations

simulation1 = Simulation(n_stations=N, discipline=discipline1, duration=100000)
simulation2 = Simulation(n_stations=N, discipline=discipline2, duration=100000)
simulation3 = Simulation(n_stations=N, discipline=discipline3, duration=100000)

results_discipline1 = simulation1.run()
results_discipline2 = simulation2.run()
results_discipline3 = simulation3.run()

print(f'Discipline 1: \n {results_discipline1}\n')
print(f'Discipline 2: \n {results_discipline2}\n')
print(f'Discipline 3: \n {results_discipline3}\n')

# %% calculate confidence intervals

ci1 = ConfidenceInterval(n_stations=N, discipline=discipline1, duration=50000, iterations=50)
ci1.calculate()
ci1.printResults("Output_discipline1.txt")

ci2 = ConfidenceInterval(n_stations=N, discipline=discipline2, duration=50000, iterations=50)
ci2.calculate()
ci2.printResults("Output_discipline2.txt")

ci3 = ConfidenceInterval(n_stations=N, discipline=discipline3, duration=50000, iterations=50)
ci3.calculate()
ci3.printResults("Output_discipline3.txt")

# %%
