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
An Action is a donor that enters or leaves a component
Nothing can be used when a staff-member needs to be freed after a certain time, but there is nothing else to be done
'''
class Action:
    ENTER = 0
    LEAVE = 1
    NOTHING = 2

    def __init__(self, component, donor, type):
        self.component = component
        self.donor = donor
        self.type = type

    def __str__(self):
        if self.type == Action.NOTHING:
            return 'No action performed'
        return f"{self.donor} {'entered' if self.type == Action.ENTER else 'left'} {self.component}"

'''
Some actions can free an occupied staff member, that is what this class is for
'''
class FreeStaffAction(Action):
    def __init__(self, component, donor, action, staff_member):
        super().__init__(component, donor, action)
        self.staff_member = staff_member

    def __str__(self):
        return super().__str__() + f' and {self.staff_member} is no longer occupied'

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

    def __init__(self, donor_type=WHOLE_BLOOD):
        self.id = Donor.ID()
        self.type = donor_type
        self.accepted = True

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
        return Subscription({'component': self, 'type': Action.ENTER})

    @property
    def LEAVE(self):
        return Subscription({'component': self, 'type': Action.LEAVE})

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
        pass
    
    def leave(self, donor):
        pass

'''
A Staff member is either a nurse or a doctor, and they generally help donors that are in a queue.
A Staff member can be activated on specific actions, or when they are freed (= no longer occupied)
'''
class StaffMember:
    def __init__(self, name):
        self.name = name
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
It contains components, but is a component itself as well
'''
class System(Component):
    def init(self):
        self.staff = []
        self.subscriptions = []
        self.arrivals = []

    def createQ(self, name):
        q = Q(name)
        return q

    def createSection(self, name):
        section = Section(name)
        return section

    def createStaff(self, name):
        member = StaffMember(name)
        self.staff.append(member)
        return member

    def subscribe(self, subscription, handler):
        self.subscriptions.append((subscription, handler))

    def add_arrival(self, time, donor):
        self.arrivals.append((time, Action(self, donor, Action.ENTER)))

    def execute_action(self, action):
        if isinstance(action, FreeStaffAction):
            action.staff_member.occupied = False

        if action.type == Action.ENTER:
            action.component.enter(action.donor)
        elif action.type == Action.LEAVE:
            action.component.leave(action.donor)
        elif action.type == Action.NOTHING:
            pass
        else:
            raise RuntimeError(f'Unknown action type: {action.type}')

    def handle_event(self, event):
        action_queue = [event.action]
        index = 0

        self.execute_action(event.action)
        execution_index = 1

        # All actions that are added to the queue will be executed as soon as possible,
        # but the actions will be checked one-by-one for subscriptions
        while index < len(action_queue):
            action = action_queue[index]
            index += 1

            # call staff member subscriptions
            for member in self.staff:
                builder = ActionBuilder(donor=action.donor)
                member.handle_action(event.time, action, builder)
                action_queue.extend(builder.actions)

                # execute all new actions
                while execution_index < len(action_queue):
                    self.execute_action(action_queue[execution_index])
                    execution_index += 1

            # call subscriptions
            for subscription, handler in self.subscriptions:
                if not subscription.is_conform(action):
                    continue
                
                builder = ActionBuilder(donor=action.donor)
                handler(event.time, action, builder)
                action_queue.extend(builder.actions)

                # execute all new actions
                while execution_index < len(action_queue):
                    self.execute_action(action_queue[execution_index])
                    execution_index += 1

        # store all executed actions in the event that triggered them
        event.executed_actions = action_queue

'''
An ActionBuilder is passed to the user-defined event handlers
They can either perform an action as a direct response to the event (will be stored in event.executed_actions),
or enqueue a new event
'''
class ActionBuilder:
    def __init__(self, component=None, donor=None):
        self.component = component
        self.donor = donor
        self.actions = []

    def use_donor(self, donor):
        self.donor = donor

    def use_component(self, component):
        self.component = component

    def enter(self, component=None, donor=None, staff_member=None):
        action = self.create_action(Action.ENTER, component, donor, staff_member)
        self.actions.append(action)

    def leave(self, component=None, donor=None, staff_member=None):
        action = self.create_action(Action.LEAVE, component, donor, staff_member)
        self.actions.append(action)

    def enter_at(self, time, component=None, donor=None, staff_member=None):
        action = self.create_action(Action.ENTER, component, donor, staff_member)
        Event(time, action)

    def leave_at(self, time, component=None, donor=None, staff_member=None):
        action = self.create_action(Action.LEAVE, component, donor, staff_member)
        Event(time, action)

    def free_staff_at(self, time, staff_member):
        Event(time, FreeStaffAction(None, None, Action.NOTHING, staff_member))

    def create_action(self, type, component=None, donor=None, staff_member=None):
        component, donor = self.resolve(component, donor)
        action = None

        if staff_member is None:
            action = Action(component, donor, type)
        else:
            action = FreeStaffAction(component, donor, type, staff_member)

        return action
    
    def resolve(self, component=None, donor=None):
        self.ensure_complete(component, donor)
        return (self.component if component is None else component, self.donor if donor is None else donor)

    def ensure_complete(self, component=None, donor=None):
        if component is None and self.component is None:
            raise RuntimeError('A component was not provided')
        if donor is None and self.donor is None:
            raise RuntimeError('A donor was not provided')

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

        for arrival_time, action in self.system.arrivals:
            Event(arrival_time, action)

        while not EVENT_Q.is_empty():
            event = EVENT_Q.pop()
            self.time = event.time
            self.system.handle_event(event)
            self.handled_events.append(event)

        return self.handled_events