from builder import *

system = System("Blood collection site")
registration_line = system.createSection("Registration line")
question_room = system.createSection("Questionnaire room")
pre_interview_room = system.createSection("Pre-interview room")
pre_donation_room = system.createSection("Pre-donation room")
donation_room = system.createSection("Donation room")

registration_q = system.createQ("Registration")
interview_q = system.createQ("Pre-interview")
donation_q = system.createQ("Pre-donation")
connect_q = system.createQ("Connect")
disconnect_q = system.createQ("Disconnect")

receptionist = system.createStaff("Receptionist")
doctor1 = system.createStaff("Doctor 1")
doctor2 = system.createStaff("Doctor 2")
nurse1 = system.createStaff("Nurse 1")
nurse2 = system.createStaff("Nurse 2")
nurse3 = system.createStaff("Nurse 3")
nurse4 = system.createStaff("Nurse 4")

def arrive(time, donor):
    donor.enter(registration_q)
    donor.enter(registration_line)

def registration_leave(time, donor):
    print('in registration leave')
    donor.enter(question_room)

def registration_policy(nurse, time, action_builder):
    if registration_q.is_empty():
        return

    donor = registration_q.first()
    action_builder.set_donor(donor)
    nurse.occupied = True
    action_builder.leave(registration_q)
    action_builder.leave_at(registration_line, time + 50).free_staff(nurse) # TODO: make use of distribution

system.on(system.ENTER, arrive)
system.on(registration_line.LEAVE, registration_leave)

receptionist.policy = registration_policy
receptionist.subscribe(registration_q.ENTER)

simulator = Simulator(system)
print('Starting simulation')
handled_events = simulator.simulate(1000)
for handled_event in handled_events:
    print(vars(handled_event))