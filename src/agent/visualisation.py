import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

def list_steps(sequence):
    # Split the input string into lines
    lines = sequence.split("\n")
    # Extract lines that contain steps
    steps = [line.strip() for line in lines if "Step" in line]
  
    return (steps)
    

def extract_steps_with_years_events(step_lines):
    years = []
    events = []
    
    for step_line in step_lines:
        # Split the step line by the colon to separate the step number and the rest
        step_parts = step_line.split(": ", 1)
        
        if len(step_parts) < 2:
            continue  # Skip if the format is unexpected
        
        # Further split the second part by the dash to separate the year and event
        year_event = step_parts[1].split(" - ", 1)
        
        if len(year_event) < 2:
            continue  # Skip if the format is unexpected
        
        year = year_event[0].strip()  # Extract the year part
        event = year_event[1].strip()  # Extract the event part
        
        years.append((year))
        events.append(event)
    return years, events



# Function to create the plot and directly display it in Streamlit
def plot_large_timeline(sequence):
    """
    This function takes a list of years (as strings) and events and generates a visually appealing timeline.
    
    Parameters:
    years (list): A list of years (as strings) corresponding to the events.
    events (list): A list of event descriptions.
    """
    years = extract_steps_with_years_events(list_steps(sequence))[0]
    events = extract_steps_with_years_events(list_steps(sequence))[1]
    
    if len(years) != len(events):
        raise ValueError("The length of 'years' and 'events' must be the same.")
    
    # Colors for the events (to create gradient effect)
    colors = plt.cm.plasma(np.linspace(0, 1, len(years)))
    
    # Plotting the timeline
    fig, ax = plt.subplots(figsize=(18, 8))  # Larger figure size for more space

    # Adding a horizontal line to represent the timeline
    ax.plot([0, len(years)-1], [0, 0], color='gray', linewidth=2, alpha=0.5)

    # Scatter plot to mark the events with custom markers and gradient colors
    ax.scatter(range(len(years)), [0]*len(years), color=colors, s=300, zorder=3, edgecolor='black')

    # Annotating events above and below the timeline, with rotated text for better visibility
    for i, (year, event) in enumerate(zip(years, events)):
        y_pos = 0.3 if i % 2 == 0 else -0.3  # Alternate above and below the line
        ax.text(i, y_pos, event, ha='center', fontsize=9, fontweight='bold', color=colors[i], rotation=45, rotation_mode='anchor')
        ax.text(i, y_pos - 0.15 if i % 2 == 0 else y_pos + 0.15, year, ha='center', fontsize=8, color='black')

    # Adding vertical lines to connect the events to the timeline
    for i in range(len(years)):
        ax.plot([i, i], [0, 0.2 if i % 2 == 0 else -0.2], color='gray', linestyle='--', alpha=0.7)

    # Customizing the plot aesthetics
    ax.set_ylim(-0.6, 0.6)  # More vertical space for labels
    ax.get_yaxis().set_visible(False)
    ax.set_xlim(-1, len(years))
    ax.set_title('Visualisation for timeline events', fontsize=16, fontweight='bold')

    # Hide axes
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)

    # Show the plot in Streamlit using st.pyplot
    st.pyplot(fig)
