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

class Event:
    def __init__(self, time, donor, action):
        self.time = time
        self.donor = donor
        self.action = action
        self.executed_actions = []
        self.staff_member = None
        EVENT_Q.enqueue(self)

    def has_assigned_staff(self):
        return self.staff_member != None

    def free_staff(self, staff_member):
        self.staff_member = staff_member

    def __lt__(self, other):
        return self.time < other.time

class Donor:
    ID = itertools.count().__next__

    WHOLE_BLOOD = 0
    PLASMA = 1

    def __init__(self, donor_type=WHOLE_BLOOD):
        self.id = Donor.ID()
        self.type = donor_type
        self.accepted = True

    def accept(self):
        self.accepted = True

    def reject(self):
        self.accepted = False

    def __str__(self):
        return f'Donor {self.id}'

class ActionBuilder:
    def __init__(self, donor = None):
        self.donor = donor
        self.actions = []

    def set_donor(self, donor):
        self.donor = donor

    def enter(self, component):
        self.actions.append(Action.create(component, Action.ENTER))

    def leave(self, component):
        self.actions.append(Action.create(component, Action.LEAVE))

    def enter_at(self, component, time):
        return Event(time, self.donor, Action.create(component, Action.ENTER))

    def leave_at(self, component, time):
        return Event(time, self.donor, Action.create(component, Action.LEAVE))

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
        return Action.create(self, Action.ENTER) 

    @property
    def LEAVE(self):
        return Action.create(self, Action.LEAVE)

    def __str__(self):
        return self.name


class Q(Component):
    def init(self):
        self.queue = []

    def size(self):
        return len(self.queue)

    def is_empty(self):
        return self.size() == 0

    def first(self):
        return self.queue[0]

    def enter(self, donor):
        print(f'{donor} joined {self}')
        self.queue.append(donor)

    def leave(self, donor):
        try:
            self.queue.remove(donor)
            print(f'{donor} left {self}')
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
        print(f'{donor} walked into the {self}')
        self.donors.add(donor)
    
    def leave(self, donor):
        if not donor in self.donors:
            raise RuntimeError(f'{donor} cannot leave {self} because {donor} is not in there')
        print(f'{donor} walked out of the {self}')
        self.donors.remove(donor)

class StaffMember:
    def __init__(self, system, name):
        self.system = system
        self.name = name
        self.occupied = False
        self.subscriptions = set()
        self.policy = lambda x: x 

    def subscribe(self, action_code):
        self.subscriptions.add(action_code)

    def handle_event(self, action_code):
        if self.occupied or not action_code in self.subscriptions:
            return []

        builder = ActionBuilder()
        self.policy(self, self.system.time, builder)
        return builder.actions

    def __str__(self):
        return self.name

class System(Component):
    def __init__(self, name = "system"):
        super().__init__(name)
        self.staff = []
        self.components = { }
        self.event_handlers = { }
        self.time = 0
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
        member = StaffMember(self, name)
        self.staff.append(member)
        return member

    def on(self, action_code, handler):
        if not action_code in self.event_handlers:
            self.event_handlers[action_code] = handler

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
        actions = []

        for member in self.staff:
            actions.extend(member.handle_event(action_code))

        if not action_code in self.event_handlers:
            return actions
        
        builder = ActionBuilder(donor)
        handler = self.event_handlers[action_code]
        handler(self.time, builder)
        actions.extend(builder.actions)

        return actions

    def handle_event(self, event):
        self.time = event.time

        index = 0
        actions = [event.action]

        if event.has_assigned_staff():
            event.staff_member.occupied = False
            builder = ActionBuilder()
            event.staff_member.policy(event.staff_member, self.time, builder)
            actions.extend(builder.actions)

        while index < len(actions):
            action_code = actions[index]
            index += 1

            self.execute_action(event.donor, action_code)
            new_actions = self.check_handlers(event.donor, action_code)
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
        Event(40, Donor(), Action.create(self.system, Action.ENTER))