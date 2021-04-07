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

system.on(system.ENTER, arrive)

def on_leave(time, donor):
    donor.leave(registration_line)
    donor.enter(question_room)

system.on(registration_q.LEAVE, on_leave)

def registration(nurse, time):
    donor = registation_q.first()
    donor.leave_at()

receptionist.policy = registration
receptionist.subscribe(registration_q.ENTER)


simulator = Simulator(system)
handled_events = simulator.simulate(1000)
for handled_event in handled_events:
    print(vars(handled_event))