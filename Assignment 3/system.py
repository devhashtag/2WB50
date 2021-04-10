import itertools
from util import *
from abc import ABC, abstractmethod
# Global variable is a design choice: give up testability for less clutter (passing it around to objects and such)
EVENT_Q = FES()

'''
A subscription can communicate to what action you want to subscribe.
Its input is a dictionary. The handler will then only be called if the action has the same shape as self.shape
'''
class Subscription:
    def __init__(self, shape):
        self.shape = shape

    def is_conform(self, action):
        for key in self.shape:
            if not hasattr(action, key) or getattr(action, key) != self.shape[key]:
                return False
        return True
        
'''
Base object for all actions
'''
class Action(ABC):
    pass

'''
Represents a donor entering or leaving a component
'''
class DonorAction(Action):
    ENTER = 0
    LEAVE = 1

    def __init__(self, component, donor, typ):
        self.component = component
        self.donor = donor
        self.type = typ

    def __str__(self):
        return f'{self.donor} {"entered" if self.type == DonorAction.ENTER else "left"} {self.component}'

'''
A StaffAction can occupy or release/free a staff member
'''
class StaffAction(Action):
    OCCUPY = 0
    FREE = 1

    def __init__(self, staff_member, typ):
        self.staff_member = staff_member
        self.type = typ

    def __str__(self):
        if self.type == StaffAction.OCCUPY:
            return f'{self.staff_member} is occupied'
        return f'{self.staff_member} is no longer occupied'

'''
A combined actions combines a donor and a staff action as a single action.
'''
class CombinedAction(Action):
    def __init__(self, donor_action, staff_action):
        self.donor_action = donor_action
        self.staff_action = staff_action

    def __str__(self):
        return f'{self.donor_action} and {self.staff_action}'

'''
An Event is a the basis of the simulation.
It contains a timestamp and an action to be executed on that timestamp
An action can cause other actions to execute at the same time instant. We keep track of all actions in executed_actions

NOTE: Instantiating an event immediately puts it on the global event queue.
'''
class Event:
    def __init__(self, time, action):
        self.time = time
        self.action = action
        self.executed_actions = []
        EVENT_Q.enqueue(self)

    def __lt__(self, other):
        return self.time < other.time

'''
Donors go through a system. They are created once, and can then enter and leave components.
A Donor is of a donor type, and can be accepted or rejected after an interview
'''
class Donor:
    ID = itertools.count().__next__

    WHOLE_BLOOD = 0
    PLASMA = 1

    def __init__(self, time, donor_type=WHOLE_BLOOD):
        self.id = Donor.ID()
        self.type = donor_type
        self.accepted = True
        self.arrival_time = time

    def __str__(self):
        return f'Donor {self.id}'

'''
Components are the building blocks of systems. A component can be entered and left
'''
class Component(ABC):
    ID = itertools.count().__next__

    def __init__(self, name):
        self.id = Component.ID()
        self.name = name
        self.donors = set()
        self.init()

    def init(self): pass
    def enter(self, donor):
        if donor in self.donors:
            raise RuntimeError(f'{donor} cannot enter {self} because {donor} is already in {self}')
        self.donors.add(donor)

    def leave(self, donor):
        if not donor in self.donors:
            raise RuntimeError(f'{donor} cannot leave {self} because {donor} is not in {self}')
        self.donors.remove(donor)

    @property
    def ENTER(self):
        return Subscription({'component': self, 'type': DonorAction.ENTER})

    @property
    def LEAVE(self):
        return Subscription({'component': self, 'type': DonorAction.LEAVE})

    def __str__(self):
        return self.name

'''
A queue is a component that represents a queue within the system. It does not have to be physical location,
it just signifies that there is a collection of donors waiting on something
'''
class Q(Component):
    def init(self):
        self.queue = [] #TODO: If simulation is inefficient, make this an ordered set (dict without values)

    def size(self):
        return len(self.queue)

    def is_empty(self):
        return self.size() == 0

    def first(self):
        return self.queue[0]

    def first_of_type(self, donor_type):
        for donor in self.queue:
            if donor.type == donor_type:
                return donor

    def enter(self, donor):
        super().enter(donor)
        self.queue.append(donor)

    def leave(self, donor):
        super().leave(donor)
        self.queue.remove(donor)
    
    def __str__(self):
        return f'{self.name} queue'

'''
A section represents a physical location in the system.
'''
class Section(Component):
    def enter(self, donor):
        super().enter(donor)
    
    def leave(self, donor):
        super().leave(donor)

'''
A Staff member is either a nurse or a doctor, and they generally help donors that are in a queue.
A Staff member can be activated on specific actions, or when they are freed (= no longer occupied)
'''
class StaffMember:
    def __init__(self, job, name):
        self.name = name
        self.job = job
        self.occupied = False
        self.subscriptions = []
        self.policy = lambda x: x
        self.subscribe(Subscription({'staff_member': self}))

    def subscribe(self, subscription):
        self.subscriptions.append(subscription)

    def handle_action(self, time, action, action_builder):
        if self.occupied:
            return

        # The policy should only run once, so we return as soon as we find a subscription match
        for subscription in self.subscriptions:
            if subscription.is_conform(action):
                self.policy(self, time, action, action_builder)
                return    

    def __str__(self):
        return self.name

'''
The system is a collection of components and staffmembers, with user defined behaviour.
It contains components, but is a component itself as well (because donors can enter and leave)
'''
class System(Component):
    def init(self):
        self.staff = []
        self.subscriptions = []
        self.arrivals = []
        self.time = 0

    def createQ(self, name):
        q = Q(name)
        return q

    def createSection(self, name):
        section = Section(name)
        return section

    def createStaff(self, job, name):
        member = StaffMember(job, name)
        self.staff.append(member)
        return member

    def subscribe(self, subscription, handler):
        self.subscriptions.append((subscription, handler))

    def add_arrival(self, time, donor):
        self.arrivals.append((time, DonorAction(self, donor, DonorAction.ENTER)))

    def execute_action(self, action):
        if type(action) is CombinedAction:
            self.execute_action(action.donor_action)
            self.execute_action(action.staff_action)
            return

        if type(action) is StaffAction:
            if action.type == StaffAction.OCCUPY:
                action.staff_member.occupied = True
            elif action.type == StaffAction.FREE:
                action.staff_memeber.occupied = False
            else:
                raise RuntimeError(f'Unknown StaffAction type: {action.type}')
            return

        if type(action) is DonorAction:
            if action.type == DonorAction.ENTER:
                action.component.enter(action.donor)
            elif action.type == DonorAction.LEAVE:
                action.component.leave(action.donor)
            else:
                raise RuntimeError(f'Unknown DonorAction type: {action.type}')

    def check_subscriptions(self, action):
        if type(action) is CombinedAction:
            yield from self.check_subscriptions(action.donor_action)
            yield from self.check_subscriptions(action.staff_action)
            return

        for member in self.staff:
            builder = ActionBuilder()
            member.handle_action(self.time, action, builder)
            yield from builder.actions

        for subscription, handler in self.subscriptions:
            if not subscription.is_conform(action):
                continue

            builder = ActionBuilder()

            if type(action) is DonorAction:
                builder.use_donor(action.donor)
            elif type(action) is StaffAction:
                builder.use_staff(action.staff_member)

            handler(self.time, action, builder)
            yield from builder.actions

    def handle_event(self, event):
        self.time = event.time

        action_queue = [event.action]
        index = 0

        # Execute the initial action
        self.execute_action(event.action)

        # All actions that are added to the queue will be executed as soon as they are added,
        # but the actions will be checked one-by-one for subscriptions
        while index < len(action_queue):
            action = action_queue[index]
            index += 1

            response_actions = self.check_subscriptions(action)
            action_queue.extend(response_actions)

            for response_action in response_actions:
                self.execute_action(response_action)

        # store all executed actions in the event that triggered them
        event.executed_actions = action_queue


def test(n):
    if n > 10:
        yield from [0,1,2,3,4]
        yield from [4,4,4,4,4]
        return

    for i in range(n):
        yield i

for i in test(11):
    print(i)

'''
An ActionBuilder is passed to the user-defined event handlers
They can either perform an action as a direct response to the event (will be stored in event.executed_actions),
or enqueue a new event
'''
class ActionBuilder:
    def __init__(self, component=None, donor=None, staff_member=None):
        self.component = component
        self.donor = donor
        self.staff_member = staff_member
        self.actions = []
        self.action_data = { }

    # Use this donor for creating actions
    def use_donor(self, donor):
        self.donor = donor

    # Use this component for creating actions
    def use_component(self, component):
        self.component = component

    # Use this staff member for creating actions
    def use_staff(self, staff_member):
        self.staff_member = staff_member

    def enter(self, component=None, donor=None):
        component, donor, _ = self.resolve(component, donor)
        self.action_data['donor_action'] = DonorAction(component, donor, DonorAction.ENTER)
        return self

    def leave(self, component=None, donor=None):
        component, donor, _ = self.resolve(component, donor)
        self.action_data['donor_action'] = DonorAction(component, donor, DonorAction.LEAVE)
        return self

    def occupy_staff(self, staff_member=None):
        _, _, staff_member = self.resolve(staff_member=staff_member)
        self.action_data['staff_action'] = StaffAction(staff_member, StaffAction.OCCUPY)

    def free_staff(self, staff_member=None):
        _, _, staff_member = self.resolve(staff_member=staff_member)
        self.action_data['staff_action'] = StaffAction(staff_member, StaffAction.FREE)
        return self

    def at(self, time):
        self.action_data['time'] = time
        return self

    def build(self):
        action = None

        if 'donor_action' in self.action_data and 'staff_action' in self.action_data:
            action = CombinedAction(self.action_data['donor_action'], self.action_data['staff_action'])
        elif 'donor_action' in self.action_data:
            action = self.action_data['donor_action']
        elif 'staff_action' in self.action_data:
            action = self.action_data['staff_action']
        else:
            raise RuntimeError('Cannot build action, because there is no action specified')

        if 'time' in self.action_data:
            Event(self.action_data['time'], action)
        else:
            self.actions.append(action)

    def resolve(self, component=None, donor=None, staff_member=None):
        # self.ensure_complete(component, donor)
        return (
            self.component if component is None else component,
            self.donor if donor is None else donor,
            self.staff_member if staff_member is None else staff_member)

'''
A simulator takes a system object and simulates a system. It will stop when the event queue is empty
'''
class Simulator:
    def __init__(self, system):
        self.system = system
        self.time = 0 # Note: the initial value can actually be anything as events will overwrite it
        self.handled_events = []

    def simulate(self):
        EVENT_Q.clear()
        self.handled_events = []

        for arrival_time, action in self.system.arrivals:
            Event(arrival_time, action)

        while not EVENT_Q.is_empty():
            event = EVENT_Q.pop()
            self.time = event.time
            self.system.handle_event(event)
            self.handled_events.append(event)

        return self.handled_events