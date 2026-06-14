import collections


class Solution:
    def __init__(self, orders, operations ):
        self.machines_assignments = collections.defaultdict(list)
        self.orders = orders
        self.operations = operations
        self.task_assignments = {}
    def add_machine_assignment(self, machine_id, assignments):
        self.machines_assignments[machine_id] = sorted(assignments, key=lambda tup: tup[1])
        for assignment in assignments:
            self.task_assignments[assignment[0]] = assignment

    def get_schedule_length(self):
        max_finish = 0
        for (machineId, machine_assignments) in self.machines_assignments.items():
            machine_finish = self.get_machine_finished(machineId)
            if machine_finish > max_finish:
                max_finish = machine_finish
        return max_finish

    def get_machine_finished(self, machine_id):
        if len(self.machines_assignments[machine_id]) == 0 :
            return 0
        return max(self.machines_assignments[machine_id], key=lambda tup: tup[2])[2]

    def get_utilization_ca(self, machine_id):
        if len(self.machines_assignments[machine_id]) == 0:
            return 0
        return sum( (tuple[2] - tuple[1]) for tuple in self.machines_assignments[machine_id]) / self.get_machine_finished(machine_id)

    def get_avg_utilization_ca(self):
        return sum( self.get_utilization_ca(machineId) for machineId in self.machines_assignments) / len(self.machines_assignments)

    def get_load(self, machine_id):
        if len(self.machines_assignments[machine_id]) == 0:
            return 0
        return sum((tuple[2] - tuple[1]) for tuple in self.machines_assignments[machine_id]) / self.get_schedule_length()

    def get_avg_load(self):
        return sum(self.get_load(machineId) for machineId in self.machines_assignments) / len(
            self.machines_assignments)

    def get_idle_time(self, machine_id):
        return self.get_schedule_length() - sum((tuple[2] - tuple[1]) for tuple in self.machines_assignments[machine_id])

    def get_sum_idle_time(self ):
        return sum( self.get_idle_time(machine_id) for machine_id in self.machines_assignments )

    def get_order_overdue(self, order_id):
        if self.task_assignments[ self.orders[order_id].Last_Operation.Id][2] > self.orders[order_id].due_to:
            return self.task_assignments[ self.orders[order_id].Last_Operation.Id][2] - self.orders[order_id].due_to
        return 0

    def get_overall_order_overdue(self):
        return sum(self.get_order_overdue(order_id) for order_id in self.orders)

    def get_order_earliness(self,order_id):
        if self.task_assignments[self.orders[order_id].Last_Operation.Id][2] < self.orders[order_id].due_to:
            return self.orders[order_id].due_to - self.task_assignments[self.orders[order_id].Last_Operation.Id][2]
        return 0

    def get_overall_order_earliness(self):
        return sum(self.get_order_earliness(order_id) for order_id in self.orders)

    def get_order_percent_no_overdue(self):
        return sum( 1 if self.get_order_overdue(order_id) == 0 else 0 for order_id in self.orders) / len(self.orders) * 100

    def get_order_price_no_overdue(self):
        return sum(self.orders[order_id].price if self.get_order_overdue(order_id) == 0 else 0 for order_id in self.orders)

    def get_order_overdue_penalty(self):
        return sum(self.orders[order_id].one_day_overdue_penalty * self.get_order_overdue(order_id) for order_id in self.orders)

    def get_order_expansion(self, order_id ):
        earliest_start = min( self.task_assignments[operation][1] for operation in self.orders[order_id].First_Operations )
        last_finish = self.task_assignments[self.orders[order_id].Last_Operation.Id][2]

        return  last_finish - earliest_start

    def get_order_avg_expansion(self):
        return sum(self.get_order_expansion(order_id) for order_id in self.orders) / len(self.orders)