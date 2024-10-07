import matplotlib.pyplot as plt
import numpy as np

def plot_large_timeline(years, events):
    """
    This function takes a list of years and events and generates a visually appealing timeline
    for a large number of events (e.g., 25 years and 25 events).
    
    Parameters:
    years (list): A list of years corresponding to the events.
    events (list): A list of event descriptions.
    """
    
    if len(years) != len(events):
        raise ValueError("The length of 'years' and 'events' must be the same.")
    
    # Colors for the events (to create gradient effect)
    colors = plt.cm.plasma(np.linspace(0, 1, len(years)))
    
    # Plotting the timeline
    fig, ax = plt.subplots(figsize=(18, 8))  # Larger figure size for more space

    # Adding a horizontal line to represent the timeline
    ax.plot([min(years)-2, max(years)+2], [0, 0], color='gray', linewidth=2, alpha=0.5)

    # Scatter plot to mark the events with custom markers and gradient colors
    ax.scatter(years, [0]*len(years), color=colors, s=300, zorder=3, edgecolor='black')

    # Annotating events above and below the timeline, with rotated text for better visibility
    for i, (year, event) in enumerate(zip(years, events)):
        y_pos = 0.3 if i % 2 == 0 else -0.3  # Alternate above and below the line
        ax.text(year, y_pos, event, ha='center', fontsize=9, fontweight='bold', color=colors[i], rotation=45, rotation_mode='anchor')
        ax.text(year, y_pos - 0.15 if i % 2 == 0 else y_pos + 0.15, str(year), ha='center', fontsize=8, color='black')

    # Adding vertical lines to connect the events to the timeline
    for year in years:
        ax.plot([year, year], [0, 0.2 if year % 2 == 0 else -0.2], color='gray', linestyle='--', alpha=0.7)

    # Customizing the plot aesthetics
    ax.set_ylim(-0.6, 0.6)  # More vertical space for labels
    ax.get_yaxis().set_visible(False)
    ax.set_xlim(min(years) - 2, max(years) + 2)
    ax.set_title('Visualisation for timeline events', fontsize=16, fontweight='bold')

    # Hide axes
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)

    # Show the plot
    plt.tight_layout()
    plt.show()

# Example usage with 25 years and 25 events:
years = list(range(1990, 2020))
events = [f"Event {i+1}: Description" for i in range(30)]

plot_large_timeline(years, events)