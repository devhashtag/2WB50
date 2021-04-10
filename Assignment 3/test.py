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
        doctor.subscribe(interview_q.ENTER)

    for nurse in nurses:
        nurse.policy = donation_policy
        nurse.subscribe(connect_q.ENTER)
        nurse.subscribe(disconnect_q.ENTER)

def add_arrivals():
    # add plasma donor arrivals
    for t in range(opening_time, closing_time - 60, 6):
        system.add_arrival(t, Donor(t, Donor.PLASMA))
    # add whole blood donor arrivals
    arrival_times = dist_arrivals.between(opening_time, closing_time)
    for arrival_time in arrival_times:
        system.add_arrival(arrival_time, Donor(arrival_time, Donor.WHOLE_BLOOD))

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


def queue_lengths(events):
    # for bookkeeping the queue sizes
    queue_sizes = { }

    # will contain lists of tuples of form (time, queue_size)
    queues_data = { }
    
    for event in events:
        time = event.time
        queues = set()

        for action in event.executed_actions:
            if type(action) is CombinedAction:
                action = action.donor_action

            if not type(action) is DonorAction: 
                continue

            if not type(action.component) is Q:
                continue

            q = action.component
            if not q in queue_sizes:
                queue_sizes[q] = 0

            if action.type == DonorAction.ENTER:
                queue_sizes[q] += 1
            elif action.type == DonorAction.LEAVE:
                queue_sizes[q] -= 1

            if not q in queues:
                queues.add(q)

        for q in queues:
            if not q in queues_data:
                queues_data[q] = []
            queues_data[q].append((time, queue_sizes[q]))

    return queues_data

def sojourn_times(events): 
    # for saving the sojourn times
    st_blood = []
    st_plasma = []

    # cycle through all events to find donors leaving the system
    for event in events:
        time = event.time
        for action in event.executed_actions:
            if type(action) is CombinedAction:
                action = action.donor_action

            if not type(action) is DonorAction:
                continue

            if not (action.type == DonorAction.LEAVE and type(action.component) is System):
                continue
            
            donor = action.donor
            sojourn_time = time - donor.arrival_time
            if donor.type == Donor.WHOLE_BLOOD:
                st_blood.append(sojourn_time)
            elif donor.type == Donor.PLASMA:
                st_plasma.append(sojourn_time)

    return st_blood, st_plasma

def section_donors(events):
    # for saving the average number of donors per section
    sec_occupants = { }
    sec_occupants['total'] = 0

    # will contain lists of tuples of form (time, queue_size)
    sec_data = { }
    sec_data['total'] = []

    for event in events:
        time = event.time
        sec = None

        for action in event.executed_actions:
            if type(action) is CombinedAction:
                action = action.donor_action

            if not type(action) is DonorAction:
                continue

            if not type(action.component) is Section:
                continue

            sec = action.component
            if not sec in sec_occupants:
                sec_occupants[sec] = 0

            if action.type == DonorAction.ENTER:
                sec_occupants[sec] += 1
                sec_occupants['total'] += 1
            elif action.type == DonorAction.LEAVE:
                sec_occupants[sec] -= 1
                sec_occupants['total'] -= 1

        if sec != None:
            if not sec in sec_data:
                sec_data[sec] = []
            sec_data[sec].append((time, sec_occupants[sec]))
            sec_data['total'].append((time, sec_occupants['total']))

    return sec_data

def staff_occupation(events):
    # for saving the average number of donors per section
    staff_occupation = { 
        'Receptionist': 1,
        'Doctor': len(doctors),
        'Nurse': len(nurses)
    }
    # staff_occupation['total'] = 0

    # will contain lists of tuples of form (time, queue_size)
    staff_data = { }
    # staff_data['total'] = []

    for event in events:
        time = event.time
        staff = None

        for action in event.executed_actions:
            if type(action) is CombinedAction:
                action = action.staff_action

            if not (type(action) is StaffAction):
                continue

            staff = action.staff_member.job

            if action.type is StaffAction.FREE:
                staff_occupation[staff] += 1
            else:
                staff_occupation[staff] -= 1

        if staff != None:
            if not staff in staff_data:
                staff_data[staff] = []
            staff_data[staff].append((time, staff_occupation[staff]))
            # staff_data['total'].append((time, staff_occupation['total']))

    return staff_data

register_handlers()
add_arrivals()
events = simulate()

def get_mean(times, amounts):
    weighted_amounts = [ amounts[i] * (times[i+1] - times[i]) for i in range(len(times)-1)]
    return np.sum(weighted_amounts)/times[-1]

def display_ql_results(events):
    data = queue_lengths(events)

    plt.figure(figsize=(10,5))

    for queue in data.keys():
        time_stamps, sizes = zip(*data[queue])
        plt.plot(time_stamps, sizes, label=f'{queue}')

    plt.legend(loc='upper left', bbox_to_anchor=(1.0, 1.0))
    plt.title('Queue lengths during the day')
    plt.xlabel('Time (minutes)')
    plt.ylabel('Queue length')
    plt.show()

def display_st_results(events):
    st_blood, st_plasma = sojourn_times(events)
    print(f'Mean whole blood st: {np.mean(st_blood)}')
    print(f'Mean plasma st: {np.mean(st_plasma)}')

    # confidence intervals

def display_average_number_donors(events):
    data = section_donors(events)

    plt.figure(figsize=(10,5))
    time_stamps, sizes = zip(*data[registration_line])
    print(f'Registration line mean: {np.mean(sizes)}')
    print(f'normal mean: {np.mean(sizes)}')
    print(f'weighted mean: {get_mean(time_stamps, sizes)}')
    plt.plot(time_stamps, sizes, label='Registration line')

    time_stamps, sizes = zip(*data[question_room])
    print(f'Questionnaire room mean: {np.mean(sizes)}')
    print(f'normal mean: {np.mean(sizes)}')
    print(f'weighted mean: {get_mean(time_stamps, sizes)}')
    plt.plot(time_stamps, sizes, label='Questionnaire room')

    time_stamps, sizes = zip(*data[pre_interview_room])
    print(f'Pre-interview room mean: {np.mean(sizes)}')
    print(f'normal mean: {np.mean(sizes)}')
    print(f'weighted mean: {get_mean(time_stamps, sizes)}')
    plt.plot(time_stamps, sizes, label='Pre-interview room')

    time_stamps, sizes = zip(*data[pre_donation_room])
    print(f'Pre-donation room mean: {np.mean(sizes)}')
    print(f'normal mean: {np.mean(sizes)}')
    print(f'weighted mean: {get_mean(time_stamps, sizes)}')
    plt.plot(time_stamps, sizes, label='Pre-donation room')

    time_stamps, sizes = zip(*data[donation_room])
    print(f'Donation room mean: {get_mean(time_stamps, sizes)}')
    print(f'normal mean: {np.mean(sizes)}')
    print(f'weighted mean: {get_mean(time_stamps, sizes)}') 
    plt.plot(time_stamps, sizes, label='Donation room')

    time_stamps, sizes = zip(*data['total'])
    print(f'Total donors mean: {np.mean(sizes)}')
    print(f'normal mean: {np.mean(sizes)}')
    print(f'weighted mean: {get_mean(time_stamps, sizes)}')
    plt.plot(time_stamps, sizes, label='Total')

    plt.legend(loc='upper left', bbox_to_anchor=(1.0, 1.0))
    plt.title('Donors in each section during the day')
    plt.xlabel('Time (minutes)')
    plt.ylabel('Donors')
    plt.show()

def display_staff_occupation(events):
    data = staff_occupation(events)

    plt.figure(figsize=(10,5))
    time_stamps, sizes = zip(*data['Receptionist'])
    print(f'Receptionist availability mean: {np.mean(sizes)}')
    print(f'normal mean: {np.mean(sizes)}')
    print(f'weighted mean: {get_mean(time_stamps, sizes)}')
    plt.plot(time_stamps, sizes, label='Receptionist')

    time_stamps, sizes = zip(*data['Doctor'])
    print(f'Doctor availability mean: {np.mean(sizes)}')
    print(f'normal mean: {np.mean(sizes)}')
    print(f'weighted mean: {get_mean(time_stamps, sizes)}')
    plt.plot(time_stamps, sizes, label='Doctors')

    time_stamps, sizes = zip(*data['Nurse'])
    print(f'Nurse availability mean: {np.mean(sizes)}')
    print(f'normal mean: {np.mean(sizes)}')
    print(f'weighted mean: {get_mean(time_stamps, sizes)}')
    plt.plot(time_stamps, sizes, label='Nurses')

    plt.legend(loc='upper left', bbox_to_anchor=(1.0, 1.0))
    plt.title('Staff occupation during the day')
    plt.xlabel('Time (minutes)')
    plt.ylabel('Donors')
    plt.show()

display_average_number_donors(events)

# [[print(action) for action in event.executed_actions] for event in events]