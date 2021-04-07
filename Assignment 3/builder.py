'''
An event can:
    - Donor arrival
    - Enter/leave system component
    - Donor exit
'''
import itertools
from util import *
from abc import ABC, abstractmethod

EVENT_Q = FES()

class Action:
    ENTER = 0
    LEAVE = 1
    
    @staticmethod
    def create(component, action):
        return (component.id, action)

# An event can have secondary actions, for example:
# An arrival in the system (primary action) means that the donor should be moved to the registration line and in the registration queue (secondary actions)
# These implications/actions are stored and can be user-defined
class Event:
    def __init__(self, time, donor, action):
        self.time = time
        self.donor = donor
        self.action = action
        self.executed_actions = []
        self.side_effects = []
        EVENT_Q.enqueue(self)

    def with_side_effect(self, side_effect):
        self.side_effects.append(side_affect)
        return self

class Donor:
    ID = itertools.count().__next__

    WHOLE_BLOOD = 0
    PLASMA = 1

    def __init__(self, donor_type=WHOLE_BLOOD):
        self.id = Donor.ID()
        self.type = donor_type
        self.accepted = True
        self.actions = []

    def enter(self, component):
        self.actions.append(Action.create(component, Action.ENTER))

    def leave(self, component):
        self.actions.append(Action.create(component, Action.LEAVE))

    def enter_at(self, component, time):
        Event(time, self, Action.create(component, Action.ENTER))

    def leave_at(self, component, time):
        Event(time, self, Action.create(component, Action.LEAVE))

    def __str__(self):
        return f'Donor {self.id}'

class Component(ABC):
    ID = itertools.count().__next__

    def __init__(self, name):
        self.id = Component.ID()
        self.name = name
        self.init()

    def init(self): pass
    def enter(self, donor): pass
    def leave(self, donor): pass

    @property
    def ENTER(self):
        return (self.id, Action.ENTER) 

    @property
    def LEAVE(self):
        return (self.id, Action.LEAVE)

    def __str__(self):
        return self.name


class Q(Component):
    def init(self):
        self.queue = []

    def enter(self, donor):
        print(f'{donor} joined {self}')
        self.queue.append(donor)

    def first(self):
        return self.queue[0]

    def leave(self, donor):
        try:
            self.queue.remove(donor)
        except ValueError:
            raise RuntimeError(f'Cannot remove {donor} from {self} because {donor} is not in the queue')
    
    def __str__(self):
        return f'{self.name} queue'

class Section(Component):
    def init(self):
        self.donors = set()

    def enter(self, donor):
        if donor in self.donors:
            raise RuntimeError(f'{donor} cannot enter {self} because {donor} is already in there')
        self.donors.add(donor)
    
    def leave(self, donor):
        if not donor in self.donors:
            raise RuntimeError(f'{donor} cannot leave {self} because {donor} is not in there')
        self.donors.remove(donor)

class StaffMember:
    def __init__(self, name, policy=lambda x: x):
        self.name = name
        self.occupied = False
        self.subscriptions = set()
        self.policy = policy

    def subscribe(self, action_code):
        self.subscriptions.add(action_code)

    def handle_event(self, action_code):
        if not action_code in self.subscriptions:
            return []

        if not self.occupied:
            self.policy(self, event.time)

        return [] # TODO collect actions from policy

    def __str__(self):
        return self.name

class System(Component):
    def __init__(self, name = "system"):
        super().__init__(name)
        self.staff = []
        self.components = { }
        self.event_handlers = { }
        self.add_component(self)

    def add_component(self, component):
        self.components[component.id] = component

    def createQ(self, name):
        q = Q(name)
        self.add_component(q)
        return q

    def createSection(self, name):
        section = Section(name)
        self.add_component(section)
        return section

    def createStaff(self, name):
        member = StaffMember(name)
        self.staff.append(member)
        return member

    def on(self, action_code, handler):
        if not action_code in self.event_handlers:
            self.event_handlers[action_code] = []
        self.event_handlers[action_code].append(handler)

    def execute_action(self, donor, action_code):
        (component_id, action) = action_code
        if not component_id in self.components:
            raise RuntimeError(f'No component with id {component_id} exists')

        component = self.components[component_id]

        if action == Action.ENTER:
            component.enter(donor)
        elif action == Action.LEAVE:
            component.leave(donor)
        else:
            raise RuntimeError(f'Unknown action {action}, cannot execute event')

    def check_handlers(self, donor, action_code):
        if not action_code in self.event_handlers:
            return []
        
        actions = []
        for handler in self.event_handlers[action_code]:
            handler(time, donor)
            actions.extend(donor.actions)
            donor.actions = []

        for member in self.staff:
            actions.extend(member.handle_event(action_code))

        return actions

    def handle_event(self, event):
        for side_effect in event.side_effects:
            side_effect()

        index = 0
        actions = [action_code]

        while index < len(actions):
            action_code = actions[index]
            index += 1

            self.execute_action(donor, action_code)
            new_actions = self.check_handlers(donor, action_code)
            actions.extend(new_actions)

        event.executed_actions = actions

class Simulator:
    def __init__(self, system):
        self.system = system
        self.time = 0
        self.handled_events = []

    def simulate(self, max_time):
        self.add_arrivals()

        while not EVENT_Q.is_empty() and self.time < max_time:
            event = EVENT_Q.pop()
            self.time = event.time
            self.system.handle_event(event)
            self.handled_events.append(event)

        return self.handled_events

    def add_arrivals(self):
        Event(0, Donor(), Action.create(self.system, Action.ENTER))