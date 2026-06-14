import gymnasium as gym
from gymnasium import spaces
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from sb3_contrib.common.wrappers import ActionMasker
from matplotlib import rcParams
from Common.InputGenerator import create_input_dataset


class FlexibleJobShopEnv(gym.Env):
    """
    Custom Gymnasium environment for Flexible Job Shop scheduling.
    Each job consists of a sequence of operations.
    Each operation is a list of alternative machine assignments, each given as a tuple (machine_id, processing_time).
    The agent must choose both the job and which alternative to use.
    """
    def __init__(self, problem_definition=None):
        super(FlexibleJobShopEnv, self).__init__()

        self.problem_definition = problem_definition
        self.n_jobs = len(problem_definition.orders)
        self.n_machines = len(problem_definition.machines)

        # Track next operation for each job.
        self.current_ops = [0] * self.n_jobs
        self.completion_time = dict()

        # Track when each machine is available.
        self.machine_available_time = [0] * self.n_machines

        # Current simulation time.
        self.current_time = 0

        # Record scheduled operations: list of tuples
        # (job_index, machine_id, start_time, finish_time, chosen_alternative)
        self.schedule = []

        # Maximum alternatives available among all operations.
        self.max_alternatives = max(len(task) for task in problem_definition.tasks_to_machines_durations_option.values())
        self.n_tasks = len(problem_definition.tasks_to_machines_durations_option)

        self.machine_ids = []  # map action->machine_id
        self.op_ids = []  # map action->op_id
        self.alternative_durations = []  # map action->duration

        i = 0
        self.action_encoding = dict()
        self.action_decoding = dict()

        for op_id, alts in problem_definition.tasks_to_machines_durations_option.items():
            for machine_id, proc_time in alts:
                self.op_ids.append(op_id)
                self.machine_ids.append(machine_id)
                self.alternative_durations.append(proc_time)
                self.action_encoding[i] = (op_id,machine_id)
                self.action_decoding[op_id, machine_id] = i
                i = i + 1

        self.op_ids = np.array(self.op_ids, dtype=np.int32)
        self.machine_ids = np.array(self.machine_ids, dtype=np.int32)
        self.alternative_durations = np.array(self.alternative_durations, dtype=np.int32)

        self.n_actions = len(self.alternative_durations)
        self.action_space = spaces.Discrete(self.n_actions)
        self.available_ops = np.zeros(self.n_tasks, dtype=np.int8)
        self.early_time = np.zeros(self.n_actions, dtype=np.int32)
        self.action_mask = np.zeros(self.n_actions, dtype=np.int32)

        # Observation: next operation indices, machine availability, current time, and valid job mask.
        self.observation_space = spaces.Dict({
            #'current_time': spaces.Box(0, 1e5, shape=(1,), dtype=np.int32),
            'machine_available_time': spaces.Box(0, 1e5, shape=(self.n_machines,), dtype=np.int32),
            'available_ops': spaces.Box(0, 1, shape=(len(self.available_ops),), dtype=np.int8),
            #'early_time': spaces.Box(0, 1e5, shape=(len(self.early_time),), dtype=np.int32),
            'operation_time': spaces.Box(0, 1e5, shape=(len(self.alternative_durations),), dtype=np.int32),
            #'machine_ids': spaces.Box(0, self.n_machines - 1, shape=(len(self.machine_ids),), dtype=np.int32),
            #'op_ids': spaces.Box(0, self.n_tasks - 1, shape=(len(self.op_ids),), dtype=np.int32),
            #'action_mask': spaces.Box(low=0, high=1, shape=(self.n_actions,), dtype=np.int8),
        })

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.completed_ops = set()
        self.action_mask = np.zeros(self.n_actions, dtype=np.int8)
        self.machine_available_time = [0] * self.n_machines
        self.current_time = 0
        self.schedule = []
        self.available_ops = np.zeros(self.n_tasks, dtype=np.int8)
        for op_id in range(self.n_tasks):
            task = self.problem_definition.tasks[op_id]
            prerequisites = task.PreviousOperations
            if op_id not in self.completed_ops and all(pr.Id in self.completed_ops for pr in prerequisites):
                self.available_ops[op_id] = 1
                for alt_id in range(len(self.problem_definition.tasks_to_machines_durations_option[op_id])):
                    flat_idx = self.action_decoding[(op_id,alt_id)]
                    self.action_mask[flat_idx] = 1

        return self._get_obs(), {}

    def _get_obs(self):

        self.latest_obs = {
            #'current_time': np.array([self.current_time], dtype=np.int32),
            'machine_available_time': np.array(self.machine_available_time, dtype=np.int32),
            'available_ops': self.available_ops.copy(),
            #'early_time': self.early_time.copy(),
            'operation_time': self.alternative_durations.copy(),
            #'machine_ids': self.machine_ids.copy(),
            #'op_ids': self.op_ids.copy(),
            #'action_mask': self.action_mask
        }
        return self.latest_obs

    def step(self, action):
        # Action is (op_id, alt_index)
        op_id, alt_index = self._decode_action(action)

        task = self.problem_definition.tasks[op_id]

        # Check if op_id exists in the job.
        # Check if the operation is already completed.
        if op_id in self.completed_ops:
            reward = -100
            info = {"error": "Operation already completed"}
            return self._get_obs(), reward, False, False, info

        # Check prerequisites.
        prerequisites = task.PreviousOperations
        if not all(pr.Id in self.completed_ops for pr in prerequisites):
            reward = -100
            info = {"error": "Prerequisites not met"}
            return self._get_obs(), reward, False, False, info

        # Check if the alternative index is valid.
        alternatives = self.problem_definition.tasks_to_machines_durations_option[op_id]
        if not any(t[0] == alt_index for t in alternatives):
            reward = -100
            info = {"error": "Invalid alternative"}
            return self._get_obs(), reward, False, False, info

        # Process the selected alternative.
        (machine_id, processing_time) = next((t for t in alternatives if t[0] == alt_index), None)

        if prerequisites:
            prerequisites_finish = max(self.completion_time[pr.Id] for pr in prerequisites)
        else:
            prerequisites_finish = 0  # or another default value
        start_time = max(prerequisites_finish, self.machine_available_time[machine_id])
        finish_time = start_time + processing_time
        # Reward could be negative processing time.
        reward = -max(0, finish_time - self.current_time)

        # Update machine availability and simulation time.
        self.machine_available_time[machine_id] = finish_time
        self.current_time = max(self.current_time, finish_time)

        # Record the scheduled operation.
        self.schedule.append((task.Order, op_id, machine_id, start_time, finish_time, alt_index))

        # Mark the operation as completed.
        self.completed_ops.add(op_id)
        self.completion_time[op_id] = finish_time

        for next_op in task.NextOperations:

            if next_op not in self.completed_ops and all(pr.Id in self.completed_ops for pr in next_op.PreviousOperations):
                self.available_ops[next_op.Id] = 1
                successor_alternatives = self.problem_definition.tasks_to_machines_durations_option[next_op.Id]
                for (alt_id,duration) in successor_alternatives:
                    flat_idx = self.action_decoding[(next_op.Id,alt_id)]
                    self.action_mask[flat_idx] = 1
                    self.early_time[flat_idx] = max(finish_time, self.early_time[flat_idx])

        self.available_ops[task.Id] = 0
        for (alt_id,duration) in alternatives:
            flat_idx = self.action_decoding[(op_id,alt_id)]
            self.action_mask[flat_idx] = 0

        # Check if all operations in all jobs are completed.
        done = all( (self.problem_definition.orders[j].Last_Operation.Id in self.completed_ops) for j,order in enumerate(self.problem_definition.orders))
        return self._get_obs(), reward, done, False, {}

    def render(self, mode='human'):
        if mode == 'human':
            #print("Current operations (next op index for each job):", self.current_ops)
            #print("Machine available times:", self.machine_available_time)
            #print("Current simulation time:", self.current_time)
            return
        elif mode == 'visual':
            print("Current operations (next op index for each job):", self.current_ops)
            print("Machine available times:", self.machine_available_time)
            print("Current simulation time:", self.current_time)
            self.visualize_schedule()

    def _decode_action(self, action):
        (op_id, alt_id) = self.action_encoding[action]

        return op_id, alt_id

    def visualize_schedule(self):
        """Creates a Gantt chart for the scheduled operations using matplotlib."""
        if not self.schedule:
            print("No operations scheduled yet!")
            return

        rcParams['font.family'] = 'Times New Roman'
        rcParams['font.size'] = 14
        colormap = cm.get_cmap('tab10')  # або 'tab20', 'Set3', 'viridis' тощо
        job_colors = [colormap(i / self.n_jobs) for i in range(self.n_jobs)]

        fig, ax = plt.subplots(figsize=(10, 5))

        # Plot each scheduled operation.
        for job_index,op_id, machine_id, start_time, finish_time, alt_index in self.schedule:
            duration = finish_time - start_time
            ax.barh(machine_id, duration, left=start_time, height=0.4, color=job_colors[job_index],  edgecolor='gray',
            linewidth=2.0,  align='center', alpha=0.8, label=f"Order {job_index}")
            ax.text(
                start_time + duration / 2,
                machine_id,
                f"#{op_id}",
                va='center', ha='center',
                fontsize=6, color='black'
            )

        ax.set_xlabel("Time (minutes)")
        ax.set_ylabel("Machine")
        ax.set_title("Flexible Job Shop Schedule (Gantt Chart)")

        # Remove duplicate legend entries.
        handles, labels = ax.get_legend_handles_labels()
        unique = dict(zip(labels, handles))
        ax.legend(unique.values(), unique.keys())

        #plt.tight_layout()
        plt.show()

def mask_fn(env):
    return env.action_mask

# Example usage: Run one episode and visualize the schedule.
if __name__ == '__main__':

    problem_definition = create_input_dataset(500)

    import time
    start_time = time.time()

    env = FlexibleJobShopEnv(problem_definition)
    env = ActionMasker(env, mask_fn)

    obs, _ = env.reset()
    done = False
    total_reward = 0

    while not done:

        # Determine valid jobs.
        #print("Observation:", obs)

        mask = env.action_masks()
        #print("Masked actions from ActionMasker:", env.action_masks())

        valid_actions = np.flatnonzero(mask)

        #action = np.random.randint(env.env.n_actions)
        action = np.random.choice(valid_actions)
        #env.env.render(mode='visual')
        op_id, alt_id = env.unwrapped._decode_action(action)

        #print(f"Selected action → Operation ID: {op_id}, Alternative ID: {alt_id}")

        obs, reward, done, _, info = env.step(action)
        total_reward += reward
        env.render()

    print("Episode finished. Total reward:", total_reward)
    end_time = time.time()
    print(f"Total simulation time: {end_time - start_time:.2f} seconds")
    env.env.render(mode='visual')
