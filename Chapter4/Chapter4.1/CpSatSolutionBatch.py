"""Minimal jobshop example."""
import collections
import datetime

from ortools.sat.python import cp_model

from Common.GantChartVisualizer import visualize_schedule
from Common.ProblemDefinition import Operation, Order, Machine
from Common.ProblemSolution import Solution

class Timer:

    def __init__(self, round_ndigits: int = 0):
        self._start_time = datetime.datetime.now()

    def __call__(self) -> datetime.timedelta:
        return datetime.datetime.now() - self._start_time

    def __str__(self) -> str:
        return str( self() )

class SolutionCollector(cp_model.CpSolverSolutionCallback):

    def __init__(self,
                 orders,
                 operations,
                 taskToMachineAssignment,
                 machines,
                 solutionLimmit,
                 variables
        ):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.__variables = variables
        self.orders = orders
        self.operations = operations
        self.solution_limit = solutionLimmit
        self.solution_list = []
        self.taskToMachineAssignment = taskToMachineAssignment
        self.machines = machines

    def on_solution_callback(self):
        self.solution_list.append(extract_solution(
            self.orders,
            self.operations,
            self.taskToMachineAssignment,
            self.machines,
            self)
        )
        if len(self.solution_list) == self.solution_limit :
            self.StopSearch()

def extract_solution(
        orders,
        operations,
        taskToMachineAssignment,
        machines,
        variables
    ):
    assigned_jobs = collections.defaultdict(list)

    solution = Solution(orders, operations)
    for (taskId, allocations) in taskToMachineAssignment.items():
        for allocation in allocations:
            if variables.value(allocation[2]):
                assigned_jobs[allocation[4]].append((taskId, variables.value(allocation[0]), variables.value(allocation[1])))

    # Create per machine output lines.
    output = ""
    for machine in machines.keys():
        solution.add_machine_assignment(machine, assigned_jobs[machine])
    return solution

def main() -> None:

    allocate_orders_by_batch( 50 )

def allocate_orders_by_batch(order_count) -> None:

    OPERATION_AT_ORDER = 10
    BATCH_SIZE = 5 #number of orders in batch

    assigned_jobs = collections.defaultdict(list)
    assigned_tasks =  collections.defaultdict()

    timer = Timer()

    for batch in range(int(order_count / BATCH_SIZE)):
        assigned_tasks,assigned_jobs,solution_collector,status,tasks,orders, machines \
            = allocate_batch(assigned_tasks,assigned_jobs, batch, BATCH_SIZE, OPERATION_AT_ORDER, timer)


    print("Sorted stats")
    print("Solutions:" + str(len(solution_collector.solution_list)))

    # feasible or optimal solutions
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print("Solution:")

        schedule = []
        # Create one list of assigned tasks per machine.

        solution = Solution(orders, tasks)

        # Create per machine output lines.
        output = ""
        for machine in machines.keys():
            solution.add_machine_assignment( machine, assigned_jobs[machine] )

            sol_line_tasks = "Machine " + str(machine) + ": "
            sol_line = "           "

            for assigned_task in solution.machines_assignments[machine]:
                schedule.append((tasks[assigned_task[0]].Order, assigned_task[0], machine, assigned_task[1], assigned_task[2], machine))

                name = f"task_{assigned_task[0]}"
                # add spaces to output to align columns.
                sol_line_tasks += f"{name:15}"

                start = assigned_task[1]
                sol_tmp = f"[{start},{assigned_task[2]}]"
                # add spaces to output to align columns.
                sol_line += f"{sol_tmp:15}"

            sol_line += "\n"
            sol_line_tasks += "\n"
            output += sol_line_tasks
            output += sol_line

        # Finally print the solution found.
        print(f"Optimal Schedule Length: {solution.get_schedule_length()}")
        print(output)

        visualize_schedule( schedule, order_count )
    else:
        print("No solution found.")

def allocate_batch( assigned_tasks, assigned_jobs, batch, BATCH_SIZE, OPERATION_AT_ORDER,timer ):
    ORDER_COUNT = (batch + 1) * BATCH_SIZE
    OPERATION_COUNT = ORDER_COUNT * OPERATION_AT_ORDER

    # Operations/tasks
    tasks = dict()
    for i in range(OPERATION_COUNT):
        tasks[i] = Operation(i, i % OPERATION_AT_ORDER, i // OPERATION_AT_ORDER)

    for i in range(ORDER_COUNT):
        # tasks relations
        FIRST_TASK = i * OPERATION_AT_ORDER
        Operation.add_relation(tasks[FIRST_TASK + 0], tasks[FIRST_TASK + 3])
        Operation.add_relation(tasks[FIRST_TASK + 1], tasks[FIRST_TASK + 3])
        Operation.add_relation(tasks[FIRST_TASK + 2], tasks[FIRST_TASK + 3])

        Operation.add_relation(tasks[FIRST_TASK + 3], tasks[FIRST_TASK + 4])

        Operation.add_relation(tasks[FIRST_TASK + 4], tasks[FIRST_TASK + 5])

        Operation.add_relation(tasks[FIRST_TASK + 5], tasks[FIRST_TASK + 6])
        Operation.add_relation(tasks[FIRST_TASK + 5], tasks[FIRST_TASK + 7])

        Operation.add_relation(tasks[FIRST_TASK + 7], tasks[FIRST_TASK + 8])
        Operation.add_relation(tasks[FIRST_TASK + 6], tasks[FIRST_TASK + 8])

        Operation.add_relation(tasks[FIRST_TASK + 8], tasks[FIRST_TASK + 9])

    orders = dict()

    for i in range(ORDER_COUNT):
        last_operation = (i + 1) * OPERATION_AT_ORDER - 1
        first_operations = [i * OPERATION_AT_ORDER, i * OPERATION_AT_ORDER + 1, i * OPERATION_AT_ORDER + 2]
        orders[i] = Order(
            i,
            600,
            5890,
            33 / 60 / 24,
            tasks[last_operation],
            first_operations)

    MACHINES_COUNT = 7
    machines = dict()
    for i in range(MACHINES_COUNT):
        machines[i] = Machine(i, "machine" + str(i))

    tasks_to_machines_durations_option = collections.defaultdict(list)

    machine_setup_times = {
        0: {
            0: {1: 10, 2: 20},
            1: {0: 10, 2: 20},
            2: {0: 20, 1: 20}
        },
        1: {
            0: {1: 10, 2: 20},
            1: {0: 10, 2: 20},
            2: {0: 20, 1: 20}
        },
        2: {
            0: {1: 10, 2: 20},
            1: {0: 10, 2: 20},
            2: {0: 20, 1: 20}
        }
    }

    waste_price = {
        0: {
            0: {1: 10, 2: 10},
            1: {0: 20, 2: 10},
            2: {0: 20, 1: 20}
        },
        1: {
            0: {1: 10, 2: 10},
            1: {0: 20, 2: 10},
            2: {0: 20, 1: 20}
        },
        2: {
            0: {1: 10, 2: 10},
            1: {0: 20, 2: 10},
            2: {0: 20, 1: 20}
        }
    }

    for order in range(ORDER_COUNT):
        FIRST_TASK = order * OPERATION_AT_ORDER
        order_task_to_machines = {
            FIRST_TASK: [(0, 10), (1, 20)],
            FIRST_TASK + 1: [(0, 15), (1, 30)],
            FIRST_TASK + 2: [(0, 25), (1, 40)],
            FIRST_TASK + 3: [(1, 24)],
            FIRST_TASK + 4: [(2, 35)],
            FIRST_TASK + 5: [(3, 42)],
            FIRST_TASK + 6: [(4, 38)],
            FIRST_TASK + 7: [(4, 61)],
            FIRST_TASK + 8: [(5, 30)],
            FIRST_TASK + 9: [(6, 30)]
        }

        tasks_to_machines_durations_option = tasks_to_machines_durations_option | order_task_to_machines

    # Create the model.
    model = cp_model.CpModel()

    # 15 days
    # UPPER BOUND
    horizon = 120 * 24 * 60
    # add variables

    taskToMachineAssignment = collections.defaultdict(list)
    machineAllIntervals = collections.defaultdict(list)
    taskMainInterval = {}

    for (taskId, task) in enumerate(tasks):

        taskToMachineAssignment[taskId] = []

        if taskId in assigned_tasks:
            task_existing_allocation = assigned_tasks.get(taskId)

            task_start_var = model.new_constant(task_existing_allocation[1])
            task_end_var = model.new_constant(task_existing_allocation[2])

            task_assign_to_machine_var = model.new_constant(True)

            interval_var = model.new_optional_interval_var(
                task_start_var, task_existing_allocation[2] - task_existing_allocation[1], task_end_var,
                task_assign_to_machine_var,
                                "start" + str(taskId) + "machine" + str(task_existing_allocation[0])
            )

            taskToMachineAssignment[taskId].append(
                (task_start_var, task_end_var, task_assign_to_machine_var, interval_var, task_existing_allocation[0]))
            machineAllIntervals[task_existing_allocation[0]].append(interval_var)

            task_main_start_var = model.new_constant(task_existing_allocation[1])
            task_main_end_var = model.new_constant(task_existing_allocation[2])

            taskMainInterval[taskId] = (task_main_start_var, task_main_end_var)

            continue

        task_main_start_var = model.new_int_var(0, horizon, "start" + str(taskId))
        task_main_end_var = model.new_int_var(0, horizon, "finish" + str(taskId))

        ##max and min gives a tight bounds for duration variable
        max_duration = max(duration for (machine, duration) in tasks_to_machines_durations_option[taskId])
        min_duration = min(duration for (machine, duration) in tasks_to_machines_durations_option[taskId])
        task_main_duration = model.new_int_var(min_duration, max_duration, "duration" + str(taskId))

        ##interval for task ->
        overal_interval_var = model.new_interval_var(task_main_start_var, task_main_duration, task_main_end_var,
                                                     "start" + str(taskId) + "machine")
        taskMainInterval[taskId] = (task_main_start_var, task_main_end_var)

        for (machine, duration) in tasks_to_machines_durations_option[taskId]:
            task_start_var = model.new_int_var(0, horizon, "start" + str(taskId) + "machine" + str(machine))
            task_end_var = model.new_int_var(0, horizon, "start" + str(taskId) + "machine" + str(machine))
            task_assign_to_machine_var = model.new_bool_var("task" + str(taskId) + "machine" + str(machine))

            model.Add(task_main_start_var == task_start_var).only_enforce_if(task_assign_to_machine_var)
            model.Add(task_main_end_var == task_end_var).only_enforce_if(task_assign_to_machine_var)
            model.Add(task_main_duration == duration).only_enforce_if(task_assign_to_machine_var)

            interval_var = model.new_optional_interval_var(
                task_start_var, duration, task_end_var, task_assign_to_machine_var,
                "start" + str(taskId) + "machine" + str(machine)
            )

            taskToMachineAssignment[taskId].append(
                (task_start_var, task_end_var, task_assign_to_machine_var, interval_var, machine))
            machineAllIntervals[machine].append(interval_var)

    # no tasks execute at the same time at resource
    for (machineId, intervals) in machineAllIntervals.items():
        model.add_no_overlap(intervals)

    all_finishes = []
    # task could be allocated only once
    for (taskId, allocations) in taskToMachineAssignment.items():
        allocationsList = [x[2] for x in allocations]
        all_finishes.extend([x[1] for x in allocations])
        model.add_exactly_one(allocationsList)
        # model.Add(sum(allocationsList)==1)

    for (taskId, task) in tasks.items():
        if len(task.PreviousOperations) > 0:

            ends = []
            for prevTask in task.PreviousOperations:
                ends.append(taskMainInterval[prevTask.Id][1])
                model.Add(taskMainInterval[taskId][0] >= taskMainInterval[prevTask.Id][1])

            earliest_start = model.new_int_var(0, horizon, "")
            model.AddMaxEquality(earliest_start, ends)
            model.Add(taskMainInterval[taskId][0] >= earliest_start)

    objective_var = model.new_int_var(0, horizon, "makespan")
    model.add_max_equality(
        objective_var,
        all_finishes
    )

    # Creates the solver and solve.
    solver = cp_model.CpSolver()
    solution_collector = SolutionCollector(
        orders,
        tasks,
        taskToMachineAssignment,
        machines,
        50,
        []
    )
    solver.parameters.use_absl_random = False
    solver.parameters.presolve_extract_integer_enforcement = True
    solver.parameters.permute_variable_randomly = False
    solver.parameters.cut_level = 2
    solver.parameters.add_cg_cuts = True
    solver.parameters.max_integer_rounding_scaling = 2
    solver.parameters.add_clique_cuts = True
    solver.parameters.use_erwa_heuristic = True
    solver.parameters.exploit_all_lp_solution = True

    solver.parameters.num_workers = 4
    # status = solver.SearchForAllSolutions(model,solution_collector )

    model.minimize(objective_var)

    print(model.ModelStats())
    status = solver.SolveWithSolutionCallback(model, solution_collector)

    # Statistics.
    print("\nStatistics")
    print(f"  - conflicts: {solver.num_conflicts}")
    print(f"  - branches : {solver.num_branches}")
    print(f"  - wall time: {solver.wall_time}s")
    print(f"  - order count: {ORDER_COUNT}")
    print(f"  - objective: {solver.objective_value}")
    print(f'Time elapsed with previous is {timer}.')

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print("Solution:")
        # Create one list of assigned tasks per machine.

        for (taskId, allocations) in taskToMachineAssignment.items():
            for allocation in allocations:
                if solver.value(allocation[2]):
                    assigned_tasks[taskId] = (allocation[4], solver.value(allocation[0]), solver.value(allocation[1]))
                    assigned_jobs[allocation[4]].append(
                        (taskId, solver.value(allocation[0]), solver.value(allocation[1])))
    else:
        print("No solution found.")
        return

    return assigned_tasks,assigned_jobs,solution_collector,status,tasks,orders, machines

if __name__ == "__main__":
    main()
