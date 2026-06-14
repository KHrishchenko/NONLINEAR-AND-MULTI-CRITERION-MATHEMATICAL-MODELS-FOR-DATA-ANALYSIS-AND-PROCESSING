from matplotlib import cm, pyplot as plt

def visualize_schedule(schedule, n_jobs):
    """Creates a Gantt chart for the scheduled operations using matplotlib."""
    if not schedule:
        print("No operations scheduled yet!")
        return

    colormap = cm.get_cmap('tab10')  # або 'tab20', 'Set3', 'viridis' тощо
    job_colors = [colormap(i / n_jobs) for i in range(n_jobs)]

    fig, ax = plt.subplots(figsize=(10, 5))

    # Plot each scheduled operation.
    for job_index, op_id, machine_id, start_time, finish_time, alt_index in schedule:
        duration = finish_time - start_time
        ax.barh(machine_id, duration, left=start_time, height=0.4, color=job_colors[job_index], edgecolor='gray',
                linewidth=2.0, align='center', alpha=0.8, label=f"Order {job_index}")
        ax.text(
            start_time + duration / 2,
            machine_id,
            f"#{op_id}",
            va='center', ha='center',
            fontsize=6, color='black'
        )

    ax.set_xlabel("Time")
    ax.set_ylabel("Machine")
    ax.set_title("Flexible Job Shop Schedule (Gantt Chart)")

    # Remove duplicate legend entries.
    handles, labels = ax.get_legend_handles_labels()
    unique = dict(zip(labels, handles))
    ax.legend(unique.values(), unique.keys())

    plt.tight_layout()
    plt.show(block=True)