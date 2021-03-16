# %% imports
import pandas as pd
import math
import statistics
import random
import numpy as np
from scipy import stats
from numpy import array, dot
from numpy.linalg import LinAlgError
from queue import Queue
from abc import ABC, abstractmethod
from functools import partial
import matplotlib.pyplot as plt

# %% Define custom exception
class OutOfTimeError(Exception):
    pass
# %% Define class to read and process input
class InputParameters:
    def __init__(self, filename='input4.txt'):
        self.input_file = open(filename)
        self.__parse_file()
        self.__process_file()
    
    def __parse_file(self):
        self.arrival_rates = array([float(x) for x in self.input_file.readline().split()])
        self.expected_service_times = array([float(x) for x in self.input_file.readline().split()])
        self.expected_switchover_times = array([float(x) for x in self.input_file.readline().split()])
        self.limited_service_constants = array([float(x) for x in self.input_file.readline().split()])
        self.transition_matrix = array([[float(x) for x in line.split()] for line in self.input_file.readlines()])

    def __process_file(self):
        # retrieve N
        self.n = len(self.arrival_rates)

        # calculate the probabilities of leaving the system
        remainders = [1.0 - sum(row) for row in self.transition_matrix]
        self.transition_matrix = np.insert(self.transition_matrix, 0, remainders, 1)

        # create the random variables
        self.service_variables = [stats.expon(scale=mean) for mean in self.expected_service_times]
    
    def service_time(self, station_index):
        return self.service_variables[station_index].rvs()

    def switchover_time(self, station_index):
        # Switch over times are deterministic
        return self.expected_switchover_times[station_index]

# %% Define class for doing the theoretic calculations
class TheoreticCalculations:
    # Calculates the total (external + internal) arrival rate of customers for each queue
    def calc_arrival_rates(self):
        matrix = parameters.transition_matrix
        coefficients = np.delete(matrix, 0, 1).T - np.identity(parameters.n)
        solutions = -1 * array(parameters.arrival_rates).reshape((parameters.n, 1))
        try:
            gammas = np.linalg.inv(coefficients) @ solutions
            return gammas.flatten()
        except LinAlgError:
            raise Exception(
                'Infinite amount of solutions possible for the theorical total arrival rates. This usually only happens if there is a station with a self-loop of probability 1.')

    # Calculates the total network utilisation.
    def calc_network_utilisation(self):
        gammas = self.arrival_rates
        service_times = parameters.expected_service_times
        return dot(gammas, service_times)

    # Calculates the expected cycle time of the rover.
    # More precise: it is the mean time between two consecutive arrivals
    # of the rover at station i.
    def calc_cycle_time(self):
        r = sum(parameters.expected_switchover_times)
        rho = self.network_utilisation
        return r / (1 - rho)

    @property
    def arrival_rates(self):
        if not hasattr(self, '_arrival_rates'):
            self._arrival_rates = self.calc_arrival_rates()
        return self._arrival_rates

    @property
    def network_utilisation(self):
        if not hasattr(self, '_network_util'):
            self._network_util = self.calc_network_utilisation()
        return self._network_util

    @property
    def cycle_time(self):
        if not hasattr(self, '_cycle_time'):
            self._cycle_time = self.calc_cycle_time()
        return self._cycle_time

    def print_values(self):
        gammas = self.arrival_rates
        rho = self.network_utilisation
        mean_cycle_time = self.cycle_time

        print('Gammas')
        for i in range(len(gammas)):
            print(f'\t{i}\t{gammas[i]}')
        print(f'Rho: {rho}')
        print(f'Cycle time: {mean_cycle_time}')

# %% define simulation class
class Simulation(ABC):
    def __init__(self, n_stations, duration, rover_station=0, seed=42):
        random.seed(seed)
        np.random.seed(seed)
        self.n_stations = n_stations
        self.duration = duration
        self.initial_station = rover_station

    def initialize(self):
        self.stations = [Station(i) for i in range(self.n_stations)]
        self.rover_station = self.initial_station
        self.time = 0.0

    @abstractmethod
    def handleQueue(self):
        pass

    @property
    def current_station(self):
        return self.stations[self.rover_station]

    def handleCustomer(self):
        customer = self.current_station.next_customer()
        self.time += self.current_station.service_time()
        # save waiting time
        self.stations[self.rover_station].results.registerWaitingTime(customer.getWaitingTime(self.time), self.time)

        # select queue to move to
        nextQueue = random.choices(range(parameters.n+1), weights=parameters.transition_matrix[self.rover_station])
        nextStation = nextQueue[0]-1

        # add customer to next queue or let him leave the system
        if (nextStation != -1):
            self.stations[nextStation].addCustomer(customer, self.time)
        else:
            self.stations[self.rover_station].handleExit(customer, self.time)

    def nextStation(self):
        self.time += parameters.switchover_time(self.rover_station)
        self.stations[self.rover_station].results.registerCycleTime(self.time)
        self.rover_station = (self.rover_station + 1) % parameters.n

    def run(self):
        self.initialize()
        try:
            while True:
                self.handleQueue()
                self.nextStation()
        except OutOfTimeError:
            return self.showResults()

    def set_time(self, value):
        self._time = value
        self.checkTime()

    def get_time(self):
        return self._time

    def checkTime(self):
        # save queue length
        [station.saveQueueLength(self.time) for station in self.stations]

        # check for arrivals
        [station.checkArrival(self.time) for station in self.stations]

        # stop if duration has been reached
        if self.time >= self.duration:
            raise OutOfTimeError()

    time = property(get_time, set_time)

    def printQueues(self):
        [station.printQueue(self.time) for station in self.stations]

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

# %% Define the policies
class Policy1(Simulation):
    def handleQueue(self):
        while not self.current_station.is_empty:
            self.handleCustomer()

class Policy2(Simulation):
    def handleQueue(self):
        k = self.current_station.service_limit
        while k > 0 and not self.current_station.is_empty:
            self.handleCustomer()
            k -= 1

class Policy3(Simulation):
    def handleQueue(self):
        n = self.current_station.q_length
        while n > 0:
            self.handleCustomer()
            n -= 1

# %% define station class
class Station:
    def __init__(self, position):
        self.position = position
        self.queue = Queue()
        self.next_arrival = 0.0
        self.arrival_dist = stats.expon(scale=1/parameters.arrival_rates[position])
        self.service_limit = parameters.limited_service_constants[position]
        self.service_time = partial(parameters.service_time, position)
        self.calcNextArrival()
        self.results = StationResults()

    @property
    def q_length(self):
        return self.queue.qsize()

    @property
    def is_empty(self):
        return self.q_length == 0

    def next_customer(self):
        return self.queue.get()

    def checkArrival(self, time):
        if (self.next_arrival <= time):
            customer = Customer(self.next_arrival)
            self.queue.put(customer)
            self.calcNextArrival()

    def calcNextArrival(self):
        self.next_arrival += self.arrival_dist.rvs()

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
        self.queue_length_times = []
        self.sojourn_times = []
        self.cycle_points = []
        self.cycle_times = []

    def registerWaitingTime(self, waiting_time, time):
        if time > self.STEADY_STATE_BOUNDARY:
            self.waiting_times.append(waiting_time)

    def registerQueueLength(self, queue_length, time):
        if time > self.STEADY_STATE_BOUNDARY:
            self.queue_lengths.append(queue_length)
            self.queue_length_times.append(time)

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
    def __init__(self, simulation, iterations):
        self.simulation = simulation
        self.n_stations = simulation.n_stations
        self.duration = simulation.duration
        self.iterations = iterations
        self.mean_waiting_times = [[] for _ in range(self.n_stations)]

    def calculate(self):
        # run simulations
        for i in range(self.iterations):
            print(f"Run {i}")
            res = self.simulation.run()
            [self.mean_waiting_times[j].append(res['E[W]'][j]) for j in range(self.n_stations)]
        
        # calculate confidence intervals of results
        self.intervals = [stats.t.interval(0.95, len(means)-1, loc=np.mean(means), scale=stats.sem(means)) for means in self.mean_waiting_times]

    def printResults(self, file):
        with open(file, "w") as text_file:
            print(f"Mean waiting times: \n{self.mean_waiting_times}\n", file=text_file)
            print(f"Intervals: ", file=text_file)
            [print(f"{interval}", file=text_file) for interval in self.intervals]
        [print(interval) for interval in self.intervals]


# %% run simulations
parameters = InputParameters()
TheoreticCalculations().print_values()

# Generates paths for the queues
def generate_q_paths():
    # We want the transient behaviour
    steady_state_boundary = StationResults.STEADY_STATE_BOUNDARY
    StationResults.STEADY_STATE_BOUNDARY = 0

    for i in range(3):
        simulation = [Policy1, Policy2, Policy3][i](n_stations=parameters.n, duration=200)
        simulation.run()
        plt.subplots(figsize=(15,5))

        for s in range(parameters.n):
            station = simulation.stations[s]
            color = ['red', 'blue', 'green', 'black', 'cyan', 'magenta'][s]

            lengths = station.results.queue_lengths
            times = station.results.queue_length_times

            plt.plot(times, lengths, color=color, label=f'Station {s+1}')

        plt.xlabel('Time')
        plt.ylabel('Queue length (floor)')
        plt.title(f'Queue lengths with policy {i+1}')
        plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
        plt.savefig(f'queue_lengths_{i+1}')
    
    # reset back to original value
    StationResults.STEADY_STATE_BOUNDARY = steady_state_boundary

generate_q_paths()

simulation1 = Policy1(n_stations=parameters.n, duration=100000)
simulation2 = Policy2(n_stations=parameters.n, duration=100000)
simulation3 = Policy3(n_stations=parameters.n, duration=100000)

results_discipline1 = simulation1.run()
results_discipline2 = simulation2.run()
results_discipline3 = simulation3.run()

print(f'Discipline 1: \n {results_discipline1}\n')
print(f'Discipline 2: \n {results_discipline2}\n')
print(f'Discipline 3: \n {results_discipline3}\n')

# %% calculate confidence intervals

ci1 = ConfidenceInterval(Policy1(n_stations=parameters.n, duration=50000), iterations=50)
ci1.calculate()
ci1.printResults("Output_discipline1.txt")

ci2 = ConfidenceInterval(Policy2(n_stations=parameters.n, duration=50000), iterations=50)
ci2.calculate()
ci2.printResults("Output_discipline2.txt")

ci3 = ConfidenceInterval(Policy3(n_stations=parameters.n, duration=50000), iterations=50)
ci3.calculate()
ci3.printResults("Output_discipline3.txt")