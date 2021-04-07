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

'''
A Donor is an object that goes through the system. It can be in 1 queue at a time, and it can be in 1 section at a time.
Does not have to be in a section or queue at all times.
------------- Definitions

Q("Registration")
Q("Pre-interview")
Q("Pre-donation")
Q("Connect")
Q("Disconnect")

Section("Registration line")
Section("Questionnaire tables")
Section("Pre-interview room")
Section("Pre-donation room")
Section("Donation room")

Nurse("Receptionist")
Doctor("Doctor 1")
Doctor("Doctor 2")
Nurse("Nurse 1")
Nurse("Nurse 2")
Nurse("Nurse 3")
Nurse("Nurse 4")

A staff member can have a procedure that is executed when an event happens:
    Donor leaves donation room -> Nurse selects next candidate if there are any
    Donor finishes donation -> Nurse disconnects donor

Processes can occur automatically on a specific event without staff:
    Donor enters questionnaire room -> Wait for amount, leave questionnaire room (or: leave questionnaire after x minutes)
    Donor leaves questionnaire room -> Donor enters Pre-interview and enqueues in Pre-interview

# Policies are methods
Policy("Receptionist")
Policy("Interviewer")
Policy("Nurse")

Q("Registration") is initial Q

Nurse("Receptionist") consumes Q("Registration") with Policy("Receptionist")
Q("Registration") feeds Q("Pre-interview")

Policy("Receptionist"):
    in Donor
    Donor does questionnaire, takes expon.rvs() time
    Then move donor to Q("Pre-interview")


class Policy(ABC):
    def __init__(self):
        pass

    # builder methods

    @abstractmethod
    def execute(self):

class ReceptionistPolicy(Policy):





class Q:
    def __init__(self, id):
        pass

class Section:
    def __init__(self, id):
        pass

class Nurse:
    def __init__(self, id):
        pass

class Doctor:
    def __init__(self, id):
        pass


'''

# %%
import itertools
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import truncnorm, expon
from queue import Queue
from util import *
from events import *

arrival_rates = [5.76, 5.94, 7.20, 7.56, 8.28, 7.56, 5.94, 5.40, 5.22, 5.76, 6.66, 7.56, 7.74, 6.84, 6.12, 6.30, 6.84, 6.66, 10.44, 8.64, 9.18, 12.24, 12.6, 7.56]
max_rate = max(arrival_rates)

# TODO: Make limits (opening/closing time) configurable
def arrival_rate(t):
    if t < 0 or t > 720:
        raise RuntimeError(f'Time should be between {0} and {720}')

    index = 0 if t == 0 else (t-1) // 30 
    return arrival_rates[index]

# %%
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
class QHandler:
    pass


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
        self.handled_events = []
        self.opening_time = 8 * 60
        self.closing_time = 20 * 60
        self.queues = Queues()
        self.results = SimResults()
        self.available_interviewers = interviewers
        self.available_nurses = nurses
        self.available_beds_blood = beds_blood
        self.available_beds_plasma = beds_plasma

    def simulate(self, n_days):
        for i in range(n_days):
            self.simulate_day()

    def simulate_day(self):
        EVENT_Q.clear()
        self.time = self.opening_time
        self.generate_arrivals()

        while self.time < self.closing_time:
            next_event = EVENT_Q.pop()
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

    def generate_whole_blood_arrivals(self):
        generator = NNHP(arrival_rate, max_rate)
        arrivals = generator.arrivals(0, self.closing_time - self.opening_time)
        for arrival_time in arrivals:
            arriving_donor = Donor(arrival_time, Donor.WHOLE_BLOOD)
            arrival_event = ArrivalEvent(arrival_time, arriving_donor)

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
class SimResults:
    def __init__(self, n_queues):
        self.queue_results = [QueueResults() for _ in n_queues]
        self.sojourn_times = []

    def registerSojournTime(self, st):
        self.sojourn_times.append(st)

    def getSojournTimes(self):
        return self.sojourn_times

# %% 
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