from abc import ABC, abstractmethod
from util import FES

EVENT_Q = FES()

class Event(ABC):
    def __init__(self, time=None, donor=None):
        self.time = time
        self.donor = donor
        EVENT_Q.enqueue(self)

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
        # register waiting time
        sim.queues.registration_queue_res.registerWaitingTime(self.time - self.donor.waiting_time)


class QuestionaireEvent(Event):
    def handle(self, sim):
        # put donor in interview queue
        sim.queues.put_interview_waiting_room(self.donor) 
        # start waiting time
        self.donor.set_waiting_time(self.time)


class InterviewStartEvent(Event):
    def handle(self, sim):
        # set end interview time and event
        done_time = self.time + Simulation.dist_interview.rvs()
        event = InterviewStopEvent(done_time, self.donor)
        # register waiting time
        wTime = self.time - self.donor.waiting_time
        if (self.donor.donor_type == Donor.WHOLE_BLOOD):
            sim.queues.interview_waiting_room_blood_res.registerWaitingTime(wTime) 
        elif (self.donor.donor_type == Donor.PLASMA):
            sim.queues.interview_waiting_room_plasma_res.registerWaitingTime(wTime) 
        # occupy interviewer
        sim.occupy_interviewer() # TODO


class InterviewStopEvent(Event):
    def handle(self, sim):
        # put donor in donation waiting queue
        sim.queues.put_donation_queue(self.donor) 
        # start waiting time
        self.donor.set_waiting_time(self.time)
        # free interviewer
        sim.free_interviewer() # TODO


class StartConnectEvent(Event):
    def handle(self, sim):
        # set connect end time and event
        done_time = self.time + Simulation.dist_connect.rvs()
        event = EndConnectEvent(done_time, self.donor)
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


class EndConnectEvent(Event):
    def handle(self, sim):
        # set ready disconnect time and event
        if (self.donor.donor_type == Donor.WHOLE_BLOOD):
            done_time = self.time + Simulation.dist_whole_blood.rvs()
        elif (self.donor.donor_type == Donor.PLASMA):
            done_time = self.time + Simulation.dist_plasma.rvs()
        event = DisconnectReadyEvent(done_time, self.donor)
        # free nurse
        sim.free_nurse() 


class DisconnectReadyEvent(Event):
    def handle(self, sim):
        # put donor in disconnect queue
        sim.queues.put_disconnect_queue(self.donor) 
        # start waiting time
        self.donor.set_waiting_time(self.time)


class StartDisconnectEvent(Event):
    def handle(self, sim):
        # set disconnect end time and event
        done_time = self.time + Simulation.dist_disconnect.rvs()
        event = EndDisconnectEvent(done_time, self.donor)
        # register waiting time
        sim.queues.disconnect_queue_res.registerWaitingTime(wTime)
        # occupy nurse
        sim.occupy_nurse() 


class EndDisconnectEvent(Event):
    def handle(self, sim):
        # set leave time and event
        done_time = self.time + Simulation.dist_recover.rvs()
        event = LeaveEvent(done_time, self.donor)
        # free nurse
        sim.free_nurse()


class LeaveEvent(Event):
    def handle(self, sim):
        # register sojourn time
        sim.results.registerSojournTime(self.donor.get_sojourn_time(self.time))
        # free bed
        sim.free_bed(self.donor.donor_type) 