import matplotlib as plt
import numpy as np
import random
import pandas as pd
from scipy import stats
from scipy.special import comb
from matplotlib.pyplot import hist

# Model parameters
alpha = 7/10
beta = 99/100
ads = 10
slots = 5

# Calculates the revenue of an add
def revenue(ad):
    return ad**0.5

# Calculates the probability that a user clicks this ad
def clicks(ad):
    return comb(ads, ad) * (0.2**ad) * (0.8**(ads-ad))

# Calculates the expected revenue of a policy
def expected_revenue(policy):
    total_revenue = 0
    for t in range(0, slots):
        # Probability that the user is on the page after scanning t ads
        on_page = 1
        for s in range(0, t):
            click = clicks(policy[s])
            on_page *= click * alpha + (1 - click) * beta
        total_revenue += on_page * clicks(policy[t]) * revenue(policy[t])
    return total_revenue

def simulated_revenue(policy, iterations = 10000, return_revenues=False):
    matrix, start_state, stop_state = construct_chain(policy)

    revenues = []
    for i in range(iterations):
        states = simulate_chain(matrix ,start_state, stop_state)
        revenue = calculate_revenue(states)
        revenues.append(revenue)

    return revenues if return_revenues else np.mean(revenues)

def simulate_chain(matrix, start, stop):
    states = [start]
    choices = range(len(matrix))
    while states[-1] != stop:
        current_state = states[-1]
        next_state = random.choices(choices, weights=matrix[current_state]).pop()
        states.append(next_state)
    return states

# Constructs a markov chain given a policy.
# Returns a 3-tuple containing the probability matrix, starting state and end state.
def construct_chain(policy):
    # There are three states for each ad/slot, and one exit-state
    n_states = 3 * slots + 1

    # 0 is exit state
    # state 1 <= n <= slots corresponds to ad n
    # state slots < n <= 2 * slots corresponds to ad n that has been clicked
    # state 2*slots < n <= 3*slots corresponds to ad n that has not been clicked

    matrix = np.zeros((n_states, n_states))
    matrix = []
    for i in range(n_states):
        matrix.append([0] * n_states)

    for i in range(slots):
        ad = policy[i]
        state_clicked = ad + slots
        state_skipped = ad + 2 * slots

        matrix[ad][state_clicked] = clicks(ad)
        matrix[ad][state_skipped] = 1 - clicks(ad)

        if i < slots - 1:
            next_ad = policy[i + 1]
            matrix[state_clicked][next_ad] = alpha
            matrix[state_clicked][0] = 1 - alpha
            matrix[state_skipped][next_ad] = beta
            matrix[state_skipped][0] = 1 - beta
        else:
            matrix[state_clicked][0] = 1
            matrix[state_skipped][0] = 1
            
    return (matrix, policy[0], 0)

# calculates the revenue for a single simulation
def calculate_revenue(states):
    # print(f'States: {states}')
    total_revenue = 0
    for state in states:
        if slots < state <= 2 * slots:
            ad = state - slots
            total_revenue += revenue(ad)
    return total_revenue

def policy_1():
    return [i + 1 for i in range(slots)]

def policy_2():
    b = [i + 1 for i in range(ads)]
    b.sort(reverse=True, key=sort_value)
    r = np.full((ads, slots), -np.inf)

    for t in range(slots):
        fill(r, b, 0, t)

    policy = []
    for t in range(slots):
        max_ad = 0
        max_rev = 0
        for j in range(ads):
            if (r[j][t] > max_rev and j+1 not in policy):
                max_ad = j+1
                max_rev = r[j][t]
        policy.append(max_ad)
    return policy

def sort_value(ad):
    numerator = clicks(ad) * revenue(ad) 
    denominator = (1 - clicks(ad) * alpha - (1-clicks(ad)) * beta)
    return numerator / denominator

def fill(r, b, j, t):
    if ads - j < slots - t:
        return -np.inf
    ad = b[j]
    if r[ad-1, t] != -np.inf:
        return r[ad-1, t]
    if t != slots - 1:
        a = revenue(ad) * clicks(ad) + (clicks(ad) * alpha + (1 - clicks(j)) * beta) * fill(r, b, j+1, t+1)
        b = fill(r, b, j+1, t)
        r[ad-1, t] = max(a,b)
    else:
        r[ad-1, t] = clicks(ad) * revenue(ad)
    return r[ad-1, t]

def run(policy, iterations=100000):
    expected = expected_revenue(policy)
    simulated = simulated_revenue(policy, iterations)

    print(f'Expected revenue: {expected}')
    print(f'Simulated revenue: {simulated}')

def run_with_plot(policy, iterations=100000):
    expected = expected_revenue(policy)
    revenues = simulated_revenue(policy, iterations, True)
    simulated = np.mean(revenues)

    print(f'Expected revenue: {expected}')
    print(f'Simulated revenue: {simulated}')

    hist(revenues, bins=[i/2 for i in range(16)], rwidth=.99)

run_with_plot(policy_2())