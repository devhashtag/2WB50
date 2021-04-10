from system_definition import *

'''
Each event/action handler and policy has 3 arguments:
time: Float                   | The current simulation time
action: Action                | The action that triggered the call
action_builder: ActionBuilder | A helper object that lets you specify which actions and events need to happen 

Additionally, each policy has as first argument the staff member which is executing the policy
'''
# Action handlers
def on_arrive(time, action, action_builder):
    action_builder.enter(registration_q).build()
    action_builder.enter(registration_line).build()

def on_registration_leave(time, action, builder):
    builder.enter(question_room).build()
    builder.leave(question_room).at(time + dist_questionnaire.rvs()).build()

def on_questionnaire_leave(time, action, builder):
    builder.enter(pre_interview_room).build()
    builder.enter(interview_q).build()

def registration_policy(receptionist, time, action, action_builder):
    if registration_q.is_empty():
        return

    donor = registration_q.first()
    action_builder.use_donor(donor)

    action_builder.occupy_staff(receptionist).build()
    action_builder.leave(registration_q).build()
    (action_builder
        .leave(registration_line)
        .free_staff(receptionist)
        .at(time + dist_registration.rvs())
        .build())

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
        action_builder.enter(donation_q).build()
        return

    action_builder.leave(pre_donation_room).build()
    action_builder.enter(donation_room).build()
    action_builder.enter(connect_q).build()

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
    action_builder.leave(donation_q).build()
    action_builder.leave(pre_donation_room).build()
    action_builder.enter(donation_room).build()
    action_builder.enter(connect_q).build()

def on_donation_room_leave(time, action, action_builder):
    action_builder.leave(system).build()

# Policies
def interview_policy(doctor, time, action, action_builder):
    if interview_q.is_empty():
        return

    # plasma donors have priority, other than that its a FIFO queue
    donor = interview_q.first()
    for donor_ in interview_q.queue:
        if donor_.type == Donor.PLASMA:
            donor = donor_
            break
    
    action_builder.use_donor(donor_)
    action_builder.occupy_staff(doctor).build()
    action_builder.leave(interview_q).build()
    action_builder.leave(pre_interview_room).build()

    # five percent chance of getting rejected
    if np.random.random() <= 0.05:
        donor.accepted = False
        (action_builder
            .leave(system)
            .free_staff(doctor)
            .at(time + dist_interview.rvs())
            .build())
    else:
        donor.accepted = True # same as its default value, but better to be explicit than implicit
        (action_builder
            .enter(pre_donation_room)
            .free_staff(doctor)
            .at(time + dist_interview.rvs())
            .build())
        
def donation_policy(nurse, time, action, action_builder):
    # Priority 1: Disconnect donor
    if not disconnect_q.is_empty():
        donor = disconnect_q.first()
        action_builder.use_donor(donor)
        action_builder.occupy_staff(nurse).build()
        action_builder.leave(disconnect_q).build()

        disconnect_finish = time + dist_disconnect.rvs()
        action_builder.free_staff(nurse).at(disconnect_finish).build()
        action_builder.leave(donation_room).at(disconnect_finish + dist_recover.rvs()).build()

    if not connect_q.is_empty():
        # Priority 2: Connect plasma donor
        # Priority 3: Connect whole blood donor
        donor = connect_q.first_of_type(Donor.PLASMA)
        if donor is None:
            donor = connect_q.first()

        action_builder.use_donor(donor)
        action_builder.occupy_staff(nurse).build()
        action_builder.leave(connect_q).build()

        connect_finish = time + dist_connect.rvs()
        donation_duration = dist_plasma.rvs() if donor.type == Donor.PLASMA else dist_whole_blood.rvs()

        action_builder.free_staff(nurse).at(connect_finish).build()
        action_builder.enter(disconnect_q).at(connect_finish + donation_duration).build()
