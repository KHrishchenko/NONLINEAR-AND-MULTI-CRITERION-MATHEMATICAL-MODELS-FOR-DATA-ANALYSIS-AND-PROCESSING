class Operation:
    def __init__(self, id, type, order ):
        self.Id = id
        self.PreviousOperations = []
        self.NextOperations = []
        self.Type = type
        self.Order = order

    @staticmethod
    def add_relation( prev, next ):
        next.PreviousOperations.append(prev)
        prev.NextOperations.append(next)

class Order:
    def __init__(self, id, due_to, price, one_day_overdue_penalty, last_operation, first_operations ):
        self.Id = id
        self.due_to = due_to
        self.price = price
        self.one_day_overdue_penalty = one_day_overdue_penalty
        self.Last_Operation = last_operation
        self.First_Operations = first_operations

class Machine:
    def __init__(self, id, name ):
        self.Id = id
        self.Name = name

class FlexibleJobShopProblemDefinition:
    def __init__(self, machines,orders,tasks, tasks_to_machines_durations_option):
        self.machines = machines
        self.orders = orders
        self.tasks = tasks
        self.tasks_to_machines_durations_option = tasks_to_machines_durations_option
