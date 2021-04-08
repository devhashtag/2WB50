import numpy as np
from system import *
from scipy.stats import truncnorm, expon

# Create system
system = System("Blood collection site")
registration_line  = system.createSection("Registration line")
question_room      = system.createSection("Questionnaire room")
pre_interview_room = system.createSection("Pre-interview room")
pre_donation_room  = system.createSection("Pre-donation room")
donation_room      = system.createSection("Donation room")
registration_q = system.createQ("Registration")
interview_q    = system.createQ("Pre-interview")
donation_q     = system.createQ("Donation")
connect_q      = system.createQ("Connect")
disconnect_q   = system.createQ("Disconnect")
receptionist = system.createStaff("Receptionist")
doctor1      = system.createStaff("Doctor 1")
doctor2      = system.createStaff("Doctor 2")
nurse1       = system.createStaff("Nurse 1")
nurse2       = system.createStaff("Nurse 2")
nurse3       = system.createStaff("Nurse 3")
nurse4       = system.createStaff("Nurse 4")

# initialize distributions
dist_registration = truncnorm(0, np.infty, 2.0, 0.5)
dist_questionnaire = expon(scale=1/1.5)
dist_interview = truncnorm(0, np.infty, 6.0, 1.0)
dist_connect = expon(scale=1/3.0)
dist_whole_blood = truncnorm(0, np.infty, 8.5, 0.6)
dist_plasma = truncnorm(0, np.infty, 45.0, 6.0)
dist_disconnect = expon(scale=1/2.0)
dist_recover = expon(scale=1/4.0)

# Initialize resources
available_beds_plasma = 7
available_beds_blood = 7

# Define system dynamics in the rest of the file

# Parameters: current time, action to which was subscribed, action_builder to specify which actions you would like to happen
def arrive(time, action, action_builder):
    action_builder.enter(registration_q)
    action_builder.enter(registration_line)

system.subscribe(system.ENTER, arrive)

def registration_policy(nurse, time, action, action_builder):
    if registration_q.is_empty():
        return

    nurse.occupied = True
    donor = registration_q.first()
    action_builder.use_donor(donor)

    action_builder.leave(registration_q)
    action_builder.leave_at(time + dist_registration.rvs(), registration_line, staff_member=nurse)

receptionist.policy = registration_policy
receptionist.subscribe(registration_q.ENTER)

def on_registration_leave(time, action, builder):
    builder.enter(question_room)
    builder.leave_at(time + dist_questionnaire.rvs(), question_room)

system.subscribe(registration_line.LEAVE, on_registration_leave)

def on_questionnaire_leave(time, action, builder):
    builder.enter(pre_interview_room)
    builder.enter(interview_q)

system.subscribe(question_room.LEAVE, on_questionnaire_leave)

def interview_policy(doctor, time, action, action_builder):
    if interview_q.is_empty():
        return

    # plasma donors have priority, other than that its a FIFO queue
    donor = interview_q.first()
    for donor_ in interview_q.queue:
        if donor_.type == Donor.PLASMA:
            donor = donor_
            break
    
    doctor.occupied = True
    action_builder.use_donor(donor_)
    action_builder.leave(interview_q)
    action_builder.leave(pre_interview_room)

    # five percent chance of getting rejected
    if np.random.random() <= 0.05:
        donor.accepted = False
        action_builder.leave_at(time + dist_interview.rvs(), system, staff_member=doctor)
    else:
        action_builder.enter_at(time + dist_interview.rvs(), pre_donation_room, staff_member=doctor)
        
doctor1.policy = interview_policy
doctor2.policy = interview_policy
doctor1.subscribe(pre_interview_room.ENTER)
doctor2.subscribe(pre_interview_room.ENTER)

def on_pre_donation_enter(time, action, action_builder):
    global available_beds_plasma
    global available_beds_blood

    # check if there available beds and if so, occupy them
    if action.donor.type == Donor.PLASMA and available_beds_plasma > 0:
        available_beds_plasma -= 1
    elif action.donor.type == Donor.WHOLE_BLOOD and available_beds_blood > 0:
        available_beds_blood -= 1
    else:
        # no bed is available, so we join the donation_q and wait
        action_builder.enter(donation_q)
        return

    action_builder.leave(pre_donation_room)
    action_builder.enter(donation_room)
    action_builder.enter(connect_q)

system.subscribe(pre_donation_room.ENTER, on_pre_donation_enter)

def donation_policy(nurse, time, action, action_builder):
    # Priority 1: Disconnect donor
    if not disconnect_q.is_empty():
        nurse.occupied = True
        donor = disconnect_q.first()
        action_builder.use_donor(donor)
        action_builder.leave(disconnect_q)

        disconnect_finish = time + dist_disconnect.rvs()
        action_builder.free_staff_at(disconnect_finish, nurse)
        action_builder.leave_at(disconnect_finish + dist_recover.rvs(), system)
        return

    if not connect_q.is_empty():
        # Priority 2: Connect plasma donor
        # Priority 3: Connect whole blood donor
        donor = connect_q.first_of_type(Donor.PLASMA)
        if donor is None:
            donor = connect_q.first()

        nurse.occupied = True
        action_builder.use_donor(donor)
        action_builder.leave(connect_q)
        connect_finish = time + dist_connect.rvs()
        action_builder.free_staff_at(connect_finish, nurse)
        donation_duration = dist_plasma.rvs() if donor.type == Donor.PLASMA else dist_whole_blood.rvs()
        action_builder.enter_at(connect_finish + donation_duration, disconnect_q)


nurse1.policy = donation_policy
nurse2.policy = donation_policy
nurse3.policy = donation_policy
nurse4.policy = donation_policy
# Subscribe to all events of interest
nurse1.subscribe(system.LEAVE)
nurse2.subscribe(system.LEAVE)
nurse3.subscribe(system.LEAVE)
nurse4.subscribe(system.LEAVE)
nurse1.subscribe(connect_q.ENTER)
nurse2.subscribe(connect_q.ENTER)
nurse3.subscribe(connect_q.ENTER)
nurse4.subscribe(connect_q.ENTER)
nurse1.subscribe(disconnect_q.ENTER)
nurse2.subscribe(disconnect_q.ENTER)
nurse3.subscribe(disconnect_q.ENTER)
nurse4.subscribe(disconnect_q.ENTER)

def on_donor_leave(time, action, action_builder):
    global available_beds_plasma
    global available_beds_blood

    # If the donor left because it is not accepted during interview, no bed will become free
    if not action.donor.accepted:
        return

    # Check if there is a donor of the same type as the donor that left
    donor = donation_q.first_of_type(action.donor.type)
    if donor is None:
        if action.donor.type == Donor.PLASMA:
            available_beds_plasma += 1
        else:
            available_beds_blood += 1
        return

    action_builder.use_donor(donor)
    action_builder.leave(donation_q)
    action_builder.leave(pre_donation_room)
    action_builder.enter(donation_room)
    action_builder.enter(donation_q)

system.subscribe(system.LEAVE, on_donor_leave)

simulator = Simulator(system)

print('Simulation started...')
handled_events = simulator.simulate(100000)
print('Simulation finished')

def print_events(events):
    for event in events:
        print('Event')
        for action in event.executed_actions:
            print(f'\t{action}')

print_events(handled_events)