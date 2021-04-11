import math
import numpy as np
import pandas as pd
from system_definition import *
# from system_definition import create_system
from event_handlers import *
from util import *
import matplotlib.pyplot as plt
from scipy import stats

np.random.seed(3)

# Register all event handlers and policies
def register_handlers():
    system.subscribe(system.ENTER, on_arrive)
    system.subscribe(registration_line.LEAVE, on_registration_leave)
    system.subscribe(question_room.LEAVE, on_questionnaire_leave)
    system.subscribe(pre_donation_room.ENTER, on_pre_donation_enter)
    system.subscribe(donation_room.LEAVE, on_donation_room_leave)
    system.subscribe(system.LEAVE, on_donor_leave)

    for receptionist in receptionists:
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
    system.re_init()
    # add plasma donor arrivals
    num = 0
    for t in range(opening_time, closing_time - 60, 6):
        num += 1
        if np.random.random() <= 0.85:
            system.add_arrival(t, Donor(t, Donor.PLASMA))
        if num >= 110:
            break
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
    print(f'Donors in the system: {len(system.donors)}\n')
    return handled_events


def queue_lengths(events):
    # for bookkeeping the queue sizes
    queue_sizes = { }

    # will contain lists of tuples of form (time, queue_size)
    queues_data = {
        registration_q: [(480, 0)],
        interview_q:    [(480, 0)],
        donation_q:     [(480, 0)],
        connect_q:      [(480, 0)],
        disconnect_q:   [(480, 0)]
    }
    
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
                queues_data[q] = [(480, 0)]
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
    sec_occupants['Total'] = 0

    # will contain lists of tuples of form (time, queue_size)
    sec_data = { 
        registration_line:  [(480, 0)],
        question_room:      [(480, 0)],
        pre_interview_room: [(480, 0)],
        pre_donation_room:  [(480, 0)],
        donation_room:      [(480, 0)],
        'Total':            [(480, 0)]
    }

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
                sec_occupants['Total'] += 1
            elif action.type == DonorAction.LEAVE:
                sec_occupants[sec] -= 1
                sec_occupants['Total'] -= 1

        if sec != None:
            if not sec in sec_data:
                sec_data[sec] = [(480, 0)]
            sec_data[sec].append((time, sec_occupants[sec]))
            sec_data['Total'].append((time, sec_occupants['Total']))

    return sec_data

def staff_occupation(events):
    # for saving the average number of donors per section
    staff_occupation = { 
        'Receptionist': 0,
        'Doctor': 0,
        'Nurse': 0
    }
    # staff_occupation['total'] = 0

    # will contain lists of tuples of form (time, queue_size)
    staff_data = { 
        'Receptionist': [(480, 0)],
        'Doctor': [(480, 0)],
        'Nurse': [(480, 0)] 
    }
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
                staff_occupation[staff] -= 1
            else:
                staff_occupation[staff] += 1

        if staff != None:
            if not staff in staff_data:
                staff_data[staff] = []
            staff_data[staff].append((time, staff_occupation[staff]))
            # staff_data['total'].append((time, staff_occupation['total']))

    return staff_data

def bed_occupation(events):
        # for saving the average number of donors per section
    bed_occupation = { 
        'Whole blood': 0,
        'Plasma': 0
    }

    # will contain lists of tuples of form (time, queue_size)
    bed_data = {
        'Whole blood': [(480, 0)],
        'Plasma': [(480, 0)]
     }

    for event in events:
        time = event.time
        bed_type = None

        for action in event.executed_actions:
            if type(action) is CombinedAction:
                action = action.donor_action

            if not type(action) is DonorAction:
                continue
            
            if not action.component == donation_room:
                continue

            if action.donor.type == Donor.WHOLE_BLOOD:
                bed_type = 'Whole blood'
            elif action.donor.type == Donor.PLASMA:
                bed_type = 'Plasma'

            if action.type is DonorAction.ENTER:
                bed_occupation[bed_type] += 1
            else:
                bed_occupation[bed_type] -= 1

        if bed_type != None:
            if not bed_type in bed_data:
                bed_data[bed_type] = []
            bed_data[bed_type].append((time, bed_occupation[bed_type]))

    return bed_data

def get_mean(times, amounts):
    weighted_amounts = [ amounts[i] * (times[i+1] - times[i]) for i in range(len(times)-1)]
    return np.sum(weighted_amounts)/times[-1]

def fill_minutes(data):
    filled_day = {}
    for key in data:
        tuples = data[key]
        filled_day[key] = []
        for i in range(480, 1500):
            curr_minute = []
            for index in range(len(tuples)-1, -1, -1):
                time = math.floor(tuples[index][0])
                if time > i:
                    continue
                elif time == i:
                    curr_minute.append(tuples[index][1])
                elif time < i and not curr_minute == []:
                    break
                else: 
                    curr_minute.append(tuples[index][1])
                    break
            filled_day[key].append((i, np.mean(curr_minute)))
    return filled_day

def display_ql_results(data):
    plt.figure(figsize=(10,5))

    for queue in data.keys():
        time_stamps, sizes = zip(*data[queue])
        plt.plot(time_stamps, sizes, label=f'{queue}')

    plt.legend(loc='upper left', bbox_to_anchor=(1.0, 1.0))
    plt.title('Queue lengths during the day')
    plt.xlabel('Time (minutes)')
    plt.ylabel('Queue length')
    plt.savefig('default_queue_lengths.png')
    plt.show()

def display_st_results(data):
    st_blood, st_plasma = data
    print(f'Mean whole blood st: {np.mean(st_blood)}')
    print(f'Mean plasma st: {np.mean(st_plasma)}')

    # confidence intervals

def display_average_number_donors(data):
    plt.figure(figsize=(10,5))
    for section in data.keys():
        time_stamps, sizes = zip(*data[section])
        print(f'Registration line mean: {np.mean(sizes)}')
        print(f'normal mean: {np.mean(sizes)}')
        print(f'weighted mean: {get_mean(time_stamps, sizes)}')
        plt.plot(time_stamps, sizes, label=f'{section}')

    plt.legend(loc='upper left', bbox_to_anchor=(1.0, 1.0))
    plt.title('Donors in each section during the day')
    plt.xlabel('Time (minutes)')
    plt.ylabel('Donors')
    plt.savefig('default_number_donors.png')
    plt.show()

def display_staff_occupation(data):
    plt.figure(figsize=(10,5))
    for staff_member in data.keys():
        time_stamps, sizes = zip(*data[staff_member])
        print(f'Receptionist availability mean: {np.mean(sizes)}')
        print(f'normal mean: {np.mean(sizes)}')
        print(f'weighted mean: {get_mean(time_stamps, sizes)}')
        plt.plot(time_stamps, sizes, label=f'{staff_member}')

    plt.legend(loc='upper left', bbox_to_anchor=(1.0, 1.0))
    plt.title('Staff occupation during the day')
    plt.xlabel('Time (minutes)')
    plt.ylabel('Amount of occupied staff members')
    plt.savefig('default_staff_occupation.png')
    plt.show()

def calculate_staff_occupation(events):
    occupation = {}
    last_occupy = {}

    for staff in system.staff:
        occupation[staff] = [(opening_time, 0)]

    for event in events:
        for action in event.executed_actions:
            if type(action) is CombinedAction:
                action = action.staff_action

            if not type(action) is StaffAction:
                continue

            if action.type is StaffAction.OCCUPY:
                previous = occupation[action.staff_member][-1]
                occupation[action.staff_member].append((event.time, previous[1]))

            if action.type is StaffAction.FREE:
                previous = occupation[action.staff_member][-1]
                occupation[action.staff_member].append((event.time, previous[1] + (event.time - previous[0])))

    return occupation

def display_bed_occupation(data):
    plt.figure(figsize=(10,5))
    time_stamps, sizes = zip(*data['Whole blood'])
    print(f'Whole blood beds available mean: {np.mean(sizes)}')
    print(f'normal mean: {np.mean(sizes)}')
    print(f'weighted mean: {get_mean(time_stamps, sizes)}')
    plt.plot(time_stamps, sizes, label='Whole blood')

    time_stamps, sizes = zip(*data['Plasma'])
    print(f'Plasma beds availabile mean: {np.mean(sizes)}')
    print(f'normal mean: {np.mean(sizes)}')
    print(f'weighted mean: {get_mean(time_stamps, sizes)}')
    plt.plot(time_stamps, sizes, label='Plasma')

    plt.legend(loc='upper left', bbox_to_anchor=(1.0, 1.0))
    plt.title('Bed occupation during the day')
    plt.xlabel('Time (minutes)')
    plt.ylabel('Donors')
    plt.savefig('default_bed_occupation.png')
    plt.show()


def display_cumulative_occupation(data):
    plt.figure(figsize=(10,5))
    for staff in data.keys():
        print(staff)
        times, n_occupied = zip(*data[staff])
        if staff == 'Doctor':
            n_occupied = [x / len(doctors) for x in n_occupied]
        elif staff == 'Nurse':
            n_occupied = [x / len(nurses) for x in n_occupied]
        n_occupied = [100 * x for x in n_occupied]

        plt.plot(times, n_occupied, label=f'{staff}')

    plt.title('Occupation in percentages per staff type')
    plt.xlabel('Time in minutes')
    plt.ylabel('Occupation in percentages')
    plt.legend(loc='upper left', bbox_to_anchor=(1.0, 1.0))
    plt.savefig('default_occupation.png')
    plt.show()

def display_all_results(events, individual):
    if individual:
        for day in events:
            display_average_number_donors(section_donors(events[day]))
            display_ql_results(queue_lengths(events[day]))
            display_st_results(sojourn_times(events[day]))
            display_bed_occupation(bed_occupation(events[day]))
            display_staff_occupation(staff_occupation(events[day]))
            display_cumulative_occupation(events[day])
    else:
        sd = {}
        sd_per_minute = {}
        ql = {}
        ql_per_minute = {}
        bo = {}
        bo_per_minute = {}
        so = {}
        so_per_minute = {}
        st = {}
        st_mean_wb = []
        st_mean_pl = []

        for day in events:
            sd[day] = section_donors(events[day])
            ql[day] = queue_lengths(events[day])
            bo[day] = bed_occupation(events[day])
            so[day] = staff_occupation(events[day])
            st[day] = sojourn_times(events[day])

        for day in events:
            sd_per_minute[day] = fill_minutes(sd[day])
            ql_per_minute[day] = fill_minutes(ql[day])
            bo_per_minute[day] = fill_minutes(bo[day])
            so_per_minute[day] = fill_minutes(so[day])
            st_mean_wb.append(np.mean(st[day][0]))
            st_mean_pl.append(np.mean(st[day][1]))

        sd_data = combine_days(sd_per_minute)
        display_average_number_donors(sd_data)

        data = combine_days(ql_per_minute)
        display_ql_results(data)

        data = combine_days(bo_per_minute)
        display_bed_occupation(data)

        data = combine_days(so_per_minute)
        display_staff_occupation(data)
        display_cumulative_occupation(data)

        print('\n Confidence intervals:')
        st_confidence_interval_wb = stats.t.interval(0.95, len(st_mean_wb)-1, loc=np.mean(st_mean_wb), scale=stats.sem(st_mean_wb))
        st_confidence_interval_pl = stats.t.interval(0.95, len(st_mean_pl)-1, loc=np.mean(st_mean_pl), scale=stats.sem(st_mean_pl))
        print(f'Whole blood: \nMean:{np.mean(st_mean_wb)} \nCI:{st_confidence_interval_wb}')
        print(f'Plasma: \nMean:{np.mean(st_mean_pl)} \nCI:{st_confidence_interval_pl}')

        for section in sd_data:
            data = [tup[1] for tup in sd_data[section]]
            ci = stats.t.interval(0.95, len(data)-1, loc=np.mean(data), scale=stats.sem(data))
            print(f'{section}: \nMean:{np.mean(data)} \nCI:{ci}')

def combine_days(days_data):
    n_days = len(days_data)
    key_data = {}
    for key in days_data[0]:
        temp = [days_data[day][key] for day in days_data]
        values = {}
        for day in range(n_days):
            tuples = temp[day]
            values[day] = [tup[1] for tup in tuples]
        minutes = [[values[day][n] for day in range(n_days)] for n in range(len(values[0]))]
        key_data[key] = [np.mean(minute) for minute in minutes]
        key_data[key] = list(zip(range(480, 1500), key_data[key]))

    return key_data
    

def run_simulation(days):
    register_handlers()

    events_by_day = {}

    for day in range(days):
        add_arrivals()
        events = simulate()
        events_by_day[day] = events

    return events_by_day

events_by_day = run_simulation(10)
display_all_results(events_by_day, False)
