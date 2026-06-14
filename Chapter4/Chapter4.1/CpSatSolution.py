import collections

from ortools.sat.python import cp_model
from Common.GantChartVisualizer import visualize_schedule
from Common.InputGenerator import create_input_dataset
from Common.ProblemSolution import Solution

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
            self, )
        )
        if len(self.solution_list) == self.solution_limit :
            self.StopSearch()

def extract_solution(
        orders,
        operations,
        taskToMachineAssignment,
        machines,
        variables,
    ):
    assigned_jobs = collections.defaultdict(list)

    solution = Solution(orders, operations )
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
    ORDER_COUNT = 30
    allocate_orders(ORDER_COUNT)

def allocate_orders(ORDER_COUNT) -> None :
    solution,solution_collector = allocate_all(ORDER_COUNT)


def allocate_all( ORDER_COUNT ):
    problemDefinition = create_input_dataset(ORDER_COUNT)

    # Create the model.
    model = cp_model.CpModel()

    #15 days
    #UPPER BOUND
    horizon = 15 * 24 * 60
    #add variables
    taskToMachineAssignment = collections.defaultdict(list)
    machineAllIntervals = collections.defaultdict(list)
    taskMainInterval = {}
    for (taskId, task) in enumerate( problemDefinition.tasks ):
        taskToMachineAssignment[taskId] = []
        task_main_start_var = model.new_int_var(0, horizon, "start" + str(taskId))
        task_main_end_var = model.new_int_var(0, horizon, "finish" + str(taskId))

        ##max and min gives a tight bounds for duration variable
        max_duration = max( duration for ( machine, duration ) in problemDefinition.tasks_to_machines_durations_option[ taskId ])
        min_duration = min( duration for ( machine, duration ) in problemDefinition.tasks_to_machines_durations_option[ taskId ])
        task_main_duration = model.new_int_var(min_duration,max_duration, "duration" + str(taskId))

        ##interval for task ->
        taskMainInterval[taskId] = (task_main_start_var, task_main_end_var)

        for ( machine, duration ) in problemDefinition.tasks_to_machines_durations_option[ taskId ]:
            task_start_var = model.new_int_var(0, horizon, "start" + str(taskId) + "machine" + str(machine))
            task_end_var = model.new_int_var(0, horizon, "start" + str(taskId) + "machine" + str(machine) )
            task_assign_to_machine_var = model.new_bool_var("task" + str(taskId) + "machine" + str(machine) )

            model.Add(task_main_start_var == task_start_var).only_enforce_if(task_assign_to_machine_var)
            model.Add(task_main_end_var == task_end_var).only_enforce_if(task_assign_to_machine_var)
            model.Add(task_main_duration == duration).only_enforce_if(task_assign_to_machine_var)

            interval_var = model.new_optional_interval_var(
                task_start_var, duration, task_end_var, task_assign_to_machine_var, "start" + str(taskId) + "machine" + str(machine)
            )

            taskToMachineAssignment[taskId].append( ( task_start_var,task_end_var,task_assign_to_machine_var,interval_var, machine ) )
            machineAllIntervals[machine].append(interval_var)

    #no tasks execute at the same time at resource
    for (machineId, intervals) in machineAllIntervals.items():
        model.add_no_overlap(intervals)

    all_finishes = []
    #task could be allocated only once
    for ( taskId, allocations) in taskToMachineAssignment.items():
        allocationsList = [x[2] for x in allocations]
        all_finishes.extend([x[1] for x in allocations])
        model.add_exactly_one(allocationsList)
        #model.Add(sum(allocationsList)==1)

    for (taskId, task) in problemDefinition.tasks.items():
        if len(task.PreviousOperations) > 0:

            ends = []
            for prevTask in task.PreviousOperations:
                ends.append(taskMainInterval[prevTask.Id][1])
                model.Add( taskMainInterval[taskId][0] >= taskMainInterval[prevTask.Id][1])

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
        problemDefinition.orders,
        problemDefinition.tasks,
        taskToMachineAssignment,
        problemDefinition.machines,
        50,
        []
    )
    solver.parameters.use_absl_random = False
    solver.parameters. presolve_extract_integer_enforcement = True
    solver.parameters.permute_variable_randomly = False
    solver.parameters.cut_level = 2
    solver.parameters.add_cg_cuts = True
    solver.parameters.max_integer_rounding_scaling = 2
    solver.parameters.add_clique_cuts = True
    solver.parameters.use_erwa_heuristic = True
    solver.parameters.exploit_all_lp_solution = True


    solver.parameters.num_workers = 4
    #status = solver.SearchForAllSolutions(model,solution_collector )

    model.minimize(objective_var)

    print(model.ModelStats())
    status = solver.SolveWithSolutionCallback(model, solution_collector)


    print("Solutions:" + str(len(solution_collector.solution_list)))

    # feasible or optimal solutions
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print("Solution:")

        schedule = []
        # Create one list of assigned tasks per machine.
        assigned_jobs = collections.defaultdict(list)

        solution = Solution(problemDefinition.orders,
        problemDefinition.tasks)

        for ( taskId, allocations) in taskToMachineAssignment.items():
            for allocation in allocations:
                if solver.value(allocation[2]):
                    assigned_jobs[allocation[4]].append((taskId, solver.value(allocation[0]), solver.value(allocation[1])))


        # Create per machine output lines.
        output = ""
        for machine in problemDefinition.machines.keys():
            solution.add_machine_assignment( machine, assigned_jobs[machine] )

            sol_line_tasks = "Machine " + str(machine) + ": "
            sol_line = "           "

            for assigned_task in solution.machines_assignments[machine]:
                schedule.append((  problemDefinition.tasks[assigned_task[0]].Order, assigned_task[0], machine, assigned_task[1],
                                 assigned_task[2], machine))

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

        visualize_schedule(schedule, ORDER_COUNT)
    else:
        print("No solution found.")

    # Statistics.
    print("\nStatistics")
    print(f"  - conflicts: {solver.num_conflicts}")
    print(f"  - branches : {solver.num_branches}")
    print(f"  - wall time: {solver.wall_time}s")



    return  solution, solution_collector

if __name__ == "__main__":
    main()
