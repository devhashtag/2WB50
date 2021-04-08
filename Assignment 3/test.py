import numpy as np
from system_definition import *
from event_handlers import *
from util import *

# Register all event handlers and policies
def register_handlers():
    system.subscribe(system.ENTER, on_arrive)
    system.subscribe(registration_line.LEAVE, on_registration_leave)
    system.subscribe(question_room.LEAVE, on_questionnaire_leave)
    system.subscribe(pre_donation_room.ENTER, on_pre_donation_enter)
    system.subscribe(system.LEAVE, on_donor_leave)

    receptionist.policy = registration_policy
    receptionist.subscribe(registration_q.ENTER)

    for doctor in [doctor1, doctor2]:
        doctor.policy = interview_policy
        doctor.subscribe(pre_interview_room.ENTER)

    for nurse in [nurse1, nurse2, nurse3, nurse4]:
        nurse.policy = donation_policy
        nurse.subscribe(connect_q.ENTER)
        nurse.subscribe(disconnect_q.ENTER)

def add_arrivals():
    # add plasma donor arrivals
    for t in range(opening_time, closing_time - 60, 6):
        system.add_arrival(t, Donor(Donor.PLASMA))
    # add whole blood donor arrivals
    arrival_times = dist_arrivals.between(opening_time, closing_time)
    for arrival_time in arrival_times:
        system.add_arrival(arrival_time, Donor(Donor.WHOLE_BLOOD))


def simulate():
    simulator = Simulator(system)
    handled_events = simulator.simulate()

    print_events(handled_events)

    print(f'Closing time:      {to_time(simulator.time)}')
    print(f'Number of donors:  {Donor.ID()}')
    print(f'Number of events:  {len(handled_events)}')
    print(f'Number of actions: {sum([len(event.executed_actions) for event in handled_events])}')

    print('')
    print(f'Donors in the system: {len(system.donors)}')

def print_events(events):
    for event in events:
        print('Event')
        for action in event.executed_actions:
            print(f'\t{action}')

register_handlers()
add_arrivals()
simulate()