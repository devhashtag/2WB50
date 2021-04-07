'''
Method/Event for arriving donors to the system
    -Whole donors
    -Plasma donors
    -Waits until registration queue is empty
Method/Event for donors to check in at reception
    -Registration: Normal distrubtion Mean:2.0 and SS: 0.5
    -Recieves Questionaire
Method/Event for donors receiving and filling questionaire
    -Questionaire exponential distrubtion with mean: 1.5
    -After donor takes place in waiting room
Method/Event Waiting room
    -Donors waits until doctor is available for interview
    -The queue is in FCFS (First-come-first-served)
    -Plasma donors always have priority over whole blood donors
    -After the donor will have an interview with 1 doctor
Method/Event for Interview
    -Doctor is occupied
    -Normal distrubtion
    -After doctor is free
    -After Donor is 5% are out/ 95% are back in waiting room or are brought to an available bed
Method/Event for waiting for bed
    -FCFS
    -Wait for plasma bed to be available for plasma donor
    -Wait for whole blood bed to be available for whole blood donor
    -Request available nurse for bringing donor to a bed
Method/Event for donor in bed
    -A Nurse must be available
    -Nurse becomes occupied
    -Donor and Plasma bed is unavaliable
    -Nurse is available
    -Wait until blood is transferred
Method/Event for disconnecting
    -A Nurse must be available
    -Highest priority to disconnect donor
    -Nurse becomes occupied
    -Nurse is available again
Method/Event for Recover
    -After Donor removed from system
    -Bed becomes available again
    
'''


'''
Opening hours: 8 uur - 20 uur
Schedule plasma donors: 10 per hour - one every six minutes - until one hour before closing
85% of plasma donors show up
Whole blood donation arrival: see table
5% of donors are not eligable
Staff:
    - 1 nurse @ reception
    - 2 doctors @ interview
    - 4 nurses @ donation room
7 beds for plasma donors, 7 beds for whole blood donors
Service time distributions:
    Registration:     Normal(2.0, 0.5)
    Questionnaire:    Exp(1.5)
    Interview:        Normal(6.0, 1.0)
    Nurse Connect:    Exp(3.0)
    Blood donation:   Normal(8.5, 0.6)
    Plasma donation:  Normal(45.0, 6.0)
    Nurse disconnect: Exp(2.0)
    Recover:          Exp(4.0)
    

'''

'''
Sojourn times of whole blood donors and plasma donors
Average number of donors in eacht of the sections
Number of donors throughout the day and per room, how do they vary
Thoughout the day, what percentage of time is each staff member occupied

Recommendations to improve the blood bank
'''

'''
Report (7 pages):

Thorough motivation and to the point description of the blood bank
High-level summary of simulation followed by a detailed description of the components
Many well-designed plots
Extensive analyses and discussions
Several concrete recommendations for improvement, quantify the effects
Copy of the code
'''

# %%

import heapq
import itertools
import matplotlib.pyplot as plt
import numpy as np
from abc import ABC, abstractmethod
from scipy.stats import truncnorm, expon
from queue import Queue
import NHPP

arrival_rates = [5.76, 5.94, 7.20, 7.56, 8.28, 7.56, 5.94, 5.40, 5.22, 5.76, 6.66, 7.56, 7.74, 6.84, 6.12, 6.30, 6.84, 6.66, 10.44, 8.64, 9.18, 12.24, 12.6, 7.56]
max_rate = max(arrival_rates)

# TODO: Make limits (opening/closing time) configurable
def arrival_rate(t):
    if t < 0 or t > 720:
        raise RuntimeError(f'Time should be between {0} and {720}')

    index = 0 if t == 0 else (t-1) // 30 
    return arrival_rates[index]

def to_time(minutes):
    return f'{minutes // 60}:{minutes % 60}'

# copied and adapted from lecture notes


class FES:
    def __init__(self):
        self.events = []

    def push(self, event):
        heapq.heappush(self.events, event)

    def pop(self):
        self.ensure_not_empty()
        return heapq.heappop(self.events)

    def peek(self):
        self.ensure_not_empty()
        return self.events[0]

    def ensure_not_empty(self):
        if len(self.events) == 0:
            raise RuntimeError('The queue is empty')


class Donor:
    ID = itertools.count().__next__

    WHOLE_BLOOD = 0
    PLASMA = 1

    def __init__(self, time, donor_type=WHOLE_BLOOD):
        self.id = Donor.ID()
        self.arrival_time = time
        self.donor_type = donor_type

    def set_waiting_time(self, time):
        self.waiting_time = time

    def get_sojourn_time(self, time):
        return time - self.arrival_time

# %%

class Simulation:

    dist_registration = truncnorm(0, np.infty, 2.0, 0.5)
    dist_questionnaire = expon(scale=1/1.5)
    dist_interview = truncnorm(0, np.infty, 6.0, 1.0)
    dist_connect = expon(scale=1/3.0)
    dist_whole_blood = truncnorm(0, np.infty, 8.5, 0.6)
    dist_plasma = truncnorm(0, np.infty, 45.0, 6.0)
    dist_disconnect = expon(scale=1/2.0)
    dist_recover = expon(scale=1/4.0)

    def __init__(self, interviewers=2, nurses=4, beds_blood=7, beds_plasma=7):
        self.event_q = FES()
        self.handled_events = []
        self.opening_time = 8 * 60
        self.closing_time = 20 * 60
        self.queues = Queues()
        self.results = SimResults()
        self.available_interviewers = interviewers
        self.available_nurses = nurses
        self.available_beds_blood = beds_blood
        self.available_beds_plasma = beds_plasma

    def register_event(self, event):
        event.belongs_in(self.event_q)

    def simulate(self, n_days):
        for i in range(n_days):
            self.simulate_day()

    def simulate_day(self):
        self.time = self.opening_time

        self.generate_arrivals()

        while self.time < self.closing_time:
            next_event = self.event_q.pop()
            self.time = next_event
            next_event.handle(self)
            self.handled_events.append(next_event)

    def generate_arrivals(self):
        self.generate_plasma_arrrivals()
        self.generate_whole_blood_arrivals()

    def generate_plasma_arrrivals(self):
        for t in range(self.opening_time, self.closing_time - 60, 6):
            donor = Donor(t, Donor.PLASMA)
            arrival = ArrivalEvent(t, donor)
            self.register_event(arrival)

    def generate_whole_blood_arrivals(self):
        generator = NNHP(arrival_rate, max_rate)
        arrivals = generator.arrivals(0, self.closing_time - self.opening_time)
        for arrival_time in arrivals:
            arriving_donor = Donor(arrival_time, Donor.WHOLE_BLOOD)
            arrival_event = ArrivalEvent(arrival_time, arriving_donor)
            self.register_event(arrival_event)

    def occupy_interviewer(self):
        if self.available_interviewers > 0:
            self.available_interviewers -= 1
        else: raise RuntimeError('No interviewers available')
    
    def free_interviewer(self):
        self.available_interviewers += 1

    def occupy_nurse(self):
        if self.available_nurses > 0:
            self.available_nurses -= 1
        else: raise RuntimeError('No nurses available')

    def free_nurse(self):
        self.available_nurses += 1

    def occupy_bed(self, donor_type):
        if donor_type == Donor.WHOLE_BLOOD:
            if self.available_beds_blood > 0:
                self.available_beds_blood -= 1
            else: raise RuntimeError('No blood beds available')
        elif donor_type == Donor.PLASMA:
            if self.available_beds_plasma > 0:
                self.available_beds_plasma -= 1
            else: raise RuntimeError('No plasma beds available')

    def free_bed(self, donor_type):
        if donor_type == Donor.WHOLE_BLOOD:
            self.available_beds_blood += 1
        elif donor_type == Donor.PLASMA:
            self.available_beds_plasma += 1

# %%

class Queues:
    # Make new and empty queues
    def __init__(self):
        self.registration_queue = queue.queue()
        self.registration_queue_res = QueueResults()

        self.interview_waiting_room_blood = queue.queue()
        self.interview_waiting_room_blood_res = QueueResults()
        self.interview_waiting_room_plasma = queue.queue()
        self.interview_waiting_room_plasma_res = QueueResults()

        self.donation_blood_queue = queue.queue()
        self.donation_blood_queue_res = QueueResults()
        self.donation_plasma_queue = queue.queue()
        self.donation_plasma_queue_res = QueueResults()

        self.disconnect_queue = queue.queue()
        self.disconnect_queue_res = QueueResults()

    def put_registration_queue(self, donor):
        self.registration_queue.put(donor)

    def put_interview_waiting_room(self, donor):
        if donor.donor_type == Donor.PLASMA:
            self.interview_waiting_room_plasma.put(donor)
        else:
            self.interview_waiting_room_blood.put(donor)

    def put_donation_queue(self, donor):
        if donor.donor_type == Donor.PLASMA:
            self.donation_plasma_queue.put(donor)
        else:
            self.donation_blood_queue.put(donor)

    def put_disconnect_queue(self, donor):
        self.disconnect_queue.put(donor)

    def get_registration_queue_donor(self):
        return self.registration_queue.get()

    def get_interview_waiting_room_donor(self):
        if (self.interview_waiting_room_plasma.qsize() > 0):
            return self.interview_waiting_room_plasma.get()
        else:
            return self.interview_waiting_room_blood.get()

    def get_donation_queue(self):
        if (self.donation_plasma_queue.qsize() > 0):
            return self.donation_plasma_queue.get()
        else:
            return self.donation_blood_queue.get()

    def get_disconnect_queue(self, donor):
        return self.disconnect_queue.get()

# %%
class Event(ABC):
    def __init__(self, time=None, donor=None):
        self.time = time
        self.donor = donor
        self.FES = None

    def belongs_in(self, fes):
        if self.FES != None:
            raise RuntimeError('Event already belongs to an event queue')

        self.FES = fes
        self.FES.push(self)

    # wanneer kan je dit gebruiken? je kan toch nooit een event zichzelf laten registeren want dan heeft hij toch nog geen FES 
    # > Dit kun je gebruiken om vanuit een bestaand event een nieuw event te registreren
    def register(self, event): 
        event.belongs_in(self.FES)

    @abstractmethod
    def handle(self, sim):
        pass

    def __lt__(self, other):
        return self.time < other.time

    def __str__(self):
        return f'{self.__class__.__name__} at {to_time(self.time)}'


class ArrivalEvent(Event):
    def handle(self, sim):
        # put donor in registration queue
        sim.queues.put_registration_queue(self.donor)
        # start waiting time
        self.donor.set_waiting_time(self.time)


class CheckinEvent(Event):
    def handle(self, sim):
        # set questionaire done time and event
        done_time = self.time + Simulation.dist_questionnaire.rvs()
        event = QuestionaireEvent(done_time, self.donor)
        event.belongs_in(self.FES)
        # register waiting time
        sim.queues.registration_queue_res.registerWaitingTime(self.time - self.donor.waiting_time)
        pass


class QuestionaireEvent(Event):
    def handle(self, sim):
        # put donor in interview queue
        sim.queues.put_interview_waiting_room(self.donor) 
        # start waiting time
        self.donor.set_waiting_time(self.time)
        pass


class InterviewStartEvent(Event):
    def handle(self, sim):
        # set end interview time and event
        done_time = self.time + Simulation.dist_interview.rvs()
        event = InterviewStopEvent(done_time, self.donor)
        event.belongs_in(self.FES)
        # register waiting time
        wTime = self.time - self.donor.waiting_time
        if (self.donor.donor_type == Donor.WHOLE_BLOOD):
            sim.queues.interview_waiting_room_blood_res.registerWaitingTime(wTime) 
        elif (self.donor.donor_type == Donor.PLASMA):
            sim.queues.interview_waiting_room_plasma_res.registerWaitingTime(wTime) 
        # occupy interviewer
        sim.occupy_interviewer() # TODO
        pass


class InterviewStopEvent(Event):
    def handle(self, sim):
        # put donor in donation waiting queue
        sim.queues.put_donation_queue(self.donor) 
        # start waiting time
        self.donor.set_waiting_time(self.time)
        # free interviewer
        sim.free_interviewer() # TODO
        pass


class StartConnectEvent(Event):
    def handle(self, sim):
        # set connect end time and event
        done_time = self.time + Simulation.dist_connect.rvs()
        event = EndConnectEvent(done_time, self.donor)
        event.belongs_in(self.FES)
        # register waiting time
        wTime = self.time - self.donor.waiting_time
        if (self.donor.donor_type == Donor.WHOLE_BLOOD):
            sim.queues.donation_blood_queue_res.registerWaitingTime(wTime) 
        elif (self.donor.donor_type == Donor.PLASMA):
            sim.queues.donation_plasma_queue_res.registerWaitingTime(wTime) 
        # occupy nurse
        sim.occupy_nurse() 
        # occupy bed
        sim.occupy_bed(self.donor.donor_type) 
        pass


class EndConnectEvent(Event):
    def handle(self, sim):
        # set ready disconnect time and event
        if (self.donor.donor_type == Donor.WHOLE_BLOOD):
            done_time = self.time + Simulation.dist_whole_blood.rvs()
        elif (self.donor.donor_type == Donor.PLASMA):
            done_time = self.time + Simulation.dist_plasma.rvs()
        event = DisconnectReadyEvent(done_time, self.donor)
        event.belongs_in(self.FES)
        # free nurse
        sim.free_nurse() 
        pass


class DisconnectReadyEvent(Event):
    def handle(self, sim):
        # put donor in disconnect queue
        sim.queues.put_disconnect_queue(self.donor) 
        # start waiting time
        self.donor.set_waiting_time(self.time)
        pass


class StartDisconnectEvent(Event):
    def handle(self, sim):
        # set disconnect end time and event
        done_time = self.time + Simulation.dist_disconnect.rvs()
        event = EndDisconnectEvent(done_time, self.donor)
        event.belongs_in(self.FES)
        # register waiting time
        sim.queues.disconnect_queue_res.registerWaitingTime(wTime)
        # occupy nurse
        sim.occupy_nurse() 
        pass


class EndDisconnectEvent(Event):
    def handle(self, sim):
        # set leave time and event
        done_time = self.time + Simulation.dist_recover.rvs()
        event = LeaveEvent(done_time, self.donor)
        event.belongs_in(self.FES)
        # free nurse
        sim.free_nurse()
        pass


class LeaveEvent(Event):
    def handle(self, sim):
        # register sojourn time
        sim.results.registerSojournTime(self.donor.get_sojourn_time(self.time))
        # free bed
        sim.free_bed(self.donor.donor_type) 
        pass

# %%


class SimResults:
    def __init__(self, n_queues):
        self.queue_results = [QueueResults() for _ in n_queues]
        self.sojourn_times = []

    def registerSojournTime(self, st):
        self.sojourn_times.append(st)

    def getSojournTimes(self):
        return self.sojourn_times


# %% 
# copied and adapted from lecture notes
class QueueResults:
    MAX_QL = 10000  # maximum queue length that will be recorded

    def __ini__(self):
        self.sum_queue_lengths = 0
        self.sum_queue_lengths_squared = 0
        self.old_time = 0
        self.queue_length_histogram = zeros(self.MAX_QL + 1)
        self.sum_waiting_times = 0
        self.sum_waiting_times_squared = 0
        self.n_waiting_times = 0
        self.waiting_times = deque()

    def registerQueueLength(self, time, ql):
        self.sum_queue_lengths += ql * (time - self.old_time)
        self.sum_queue_lengths_squared += ql * ql * (time - self.old_time)
        self.queue_length_histogram[min(
            ql, self.MAX_QL)] += (time - self.old_time)
        self.old_time = time

    def registerWaitingTime(self, w):
        self.waiting_times.append(w)
        self.n_waiting_times += 1
        self.sum_waiting_times += w
        self.sum_waiting_times_squared += w * w

    def getMeanQueueLength(self):
        return self.sum_queue_lengths / self.old_time

    def getVarianceQueueLength(self):
        return self.sum_queue_lengths_squared / self.old_time - self.getMeanQueueLength()**2

    def getMeanWaitingTime(self):
        return self.sum_waiting_times / self.n_waiting_times

    def getVarianceWaitingTime(self):
        return self.sum_waiting_times_squared / self.n_waiting_times - self.getMeanWaitingTime()**2

    def getQueueLengthHistogram(self):
        return [x / self.oldTime for x in self.queue_length_histogram]

    def getWaitingTimes(self):
        return self.waiting_times

    def __str__(self):
        s = 'Mean queue length: ' + str(self.getMeanQueueLength()) + '\n'
        s += 'Variance queue length: ' + \
            str(self.getVarianceQueueLength()) + '\n'
        s += 'Mean waiting time: ' + str(self.getMeanWaitingTime()) + '\n'
        s += 'Variance waiting time: ' + \
            str(self.getVarianceWaitingTime()) + '\n'
        return s

    def histQueueLength(self, maxq=50):
        ql = self.getQueueLengthHistogram()
        maxx = maxq + 1
        plt.figure()
        plt.bar(range(0, maxx), ql[0: maxx])
        plt.ylabel('P(Q=k)')
        plt.xlabel('k')
        plt.show()

    def histWaitingTimes(self, nrBins=100):
        plt.figure()
        plt.hist(self.waiting_times, bins=nrBins, rwidth=0.8, density=True)
        plt.show()

    # def registerCycleTime(self):
    #     self.queue_at_times.append(self.sum_queue_lengths)

    # def plotQueueLenthPerHour(self):
    #     plt.figure()
    #     plt.plot(self.queue_at_times)


    #Queue length per hour


# %%
