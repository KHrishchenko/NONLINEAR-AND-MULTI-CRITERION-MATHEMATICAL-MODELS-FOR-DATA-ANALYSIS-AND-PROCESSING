import collections

from Common.ProblemDefinition import Operation, Order, Machine, FlexibleJobShopProblemDefinition

def create_input_dataset( ORDER_COUNT ):
    OPERATION_AT_ORDER = 10
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

        tasks_to_machines_durations_option = tasks_to_machines_durations_option | order_task_to_machines
    return  FlexibleJobShopProblemDefinition(machines, orders, tasks, tasks_to_machines_durations_option )