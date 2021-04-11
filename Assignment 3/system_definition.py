import numpy as np
from system import *
from scipy.stats import truncnorm, expon

system = System('Blood collection site')
registration_line  = system.createSection('Registration line')
question_room      = system.createSection('Questionnaire room')
pre_interview_room = system.createSection('Pre-interview room')
pre_donation_room  = system.createSection('Pre-donation room')
donation_room      = system.createSection('Donation room')
registration_q = system.createQ('Registration')
interview_q    = system.createQ('Pre-interview')
donation_q     = system.createQ('Donation')
connect_q      = system.createQ('Connect')
disconnect_q   = system.createQ('Disconnect')
receptionist = system.createStaff('Receptionist', 'Receptionist 1')
doctors = [
    system.createStaff('Doctor', 'Doctor 1'),
    system.createStaff('Doctor', 'Doctor 2'),
    # system.createStaff('Doctor', 'Doctor 3'),
]
nurses = [
    system.createStaff('Nurse', 'Nurse 1'),
    system.createStaff('Nurse', 'Nurse 2'),
    system.createStaff('Nurse', 'Nurse 3'),
    system.createStaff('Nurse', 'Nurse 4')
]

# Returns the arrival rate per minute of whole blood donors
def arrival_rate_at(time):
    time = round(time)
    if time < opening_time or time > closing_time:
        raise RuntimeError(f'Time should be between {opening_time} and {closing_time}')
    
    time -= opening_time
    index = 0 if time == 0 else int((time-1) // 30)

    return [5.76, 5.94, 7.20, 7.56, 8.28, 7.56, 5.94, 5.40, 5.22, 5.76, 6.66, 7.56, 7.74,\
            6.84, 6.12, 6.30, 6.84, 6.66, 10.44, 8.64, 9.18, 12.24, 12.6, 7.56][index] / 30

dist_registration = truncnorm(0, np.infty, 2.0, 0.5)
dist_questionnaire = expon(scale=1/1.5)
dist_interview = truncnorm(0, np.infty, 6.0, 1.0)
dist_connect = expon(scale=1/3.0)
dist_whole_blood = truncnorm(0, np.infty, 8.5, 0.6)
dist_plasma = truncnorm(0, np.infty, 45.0, 6.0)
dist_disconnect = expon(scale=1/2.0)
dist_recover = expon(scale=1/4.0)
dist_arrivals = NHPP(arrival_rate_at, 13/30)

opening_time = 8 * 60
closing_time = 20 * 60

available_beds_plasma = 7
available_beds_blood = 7