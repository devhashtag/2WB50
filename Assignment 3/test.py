import numpy as np
from system_definition import *
from event_handlers import *
from util import *
import matplotlib.pyplot as plt

np.random.seed(1)

# Register all event handlers and policies
def register_handlers():
    system.subscribe(system.ENTER, on_arrive)
    system.subscribe(registration_line.LEAVE, on_registration_leave)
    system.subscribe(question_room.LEAVE, on_questionnaire_leave)
    system.subscribe(pre_donation_room.ENTER, on_pre_donation_enter)
    system.subscribe(system.LEAVE, on_donor_leave)

    receptionist.policy = registration_policy
    receptionist.subscribe(registration_q.ENTER)

    for doctor in doctors:
        doctor.policy = interview_policy
        doctor.subscribe(pre_interview_room.ENTER)

    for nurse in nurses:
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

    # for event in handled_events:
    #     print('Event')
    #     for action in event.executed_actions:
    #         print(f'\t{action}')

    print(f'Closing time:      {to_time(simulator.time)}')
    print(f'Number of donors:  {Donor.ID()}')
    print(f'Number of events:  {len(handled_events)}')
    print(f'Number of actions: {sum([len(event.executed_actions) for event in handled_events])}')
    print(f'Donors in the system: {len(system.donors)}')
    return handled_events

register_handlers()
add_arrivals()
events = simulate()

def queue_lengths(events):
    # for bookkeeping the queue sizes
    queue_sizes = { }

    # will conatin lists of tuples of form (time, queue_size)
    queues_data = { }

    for event in events:
        time = event.time
        q = None

        for action in event.executed_actions:
            if not type(action.component) is Q:
                continue

            q = action.component
            if not q in queue_sizes:
                queue_sizes[q] = 0

            if action.type == Action.ENTER:
                queue_sizes[q] += 1
            elif action.type == Action.LEAVE:
                queue_sizes[q] -= 1

        if q != None:
            if not q in queues_data:
                queues_data[q] = []
            queues_data[q].append((time, queue_sizes[q]))

    return queues_data


data = queue_lengths(events)
time_stamps, sizes = zip(*data[interview_q])


plt.plot(time_stamps, sizes)
plt.title('Interview queue length against minutes')
plt.show()
