import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
import re

def list_steps(sequence):
    # Split the input string into lines
    lines = sequence.split("\n")
    # Determine the type of sequence from the first line
    sequence_type = ""
    if lines[0].startswith("The following is a timeline sequence"):
        sequence_type = "timeline"
    elif lines[0].startswith("The following is a chemical sequence"):
        sequence_type = "chemical"
    else:
        sequence_type = "other"
    
    # Extract lines that contain steps
    steps = [line.strip() for line in lines if "Step" in line]
    print(steps)
    return steps, sequence_type


def extract_timeline_events(steps):
    # Regular expression to identify timeline events, including various date formats
    pattern = r"Step \d+: (?P<date>\b(?:\d{1,4}(?:[\s\-,/\.]\d{1,2})?(?:[\s\-,/\.]\d{1,4})?|\w+ \d{1,2}, \d{4}|\d{1,4}\s?(?:BCE|CE|bc|ad|AD)?)\b) - (?P<event>.+?)"
    
    for step in steps:
        # Remove any leading or trailing asterisks and spaces
        step = step.strip('*').strip()
        # Each step is a string containing the date and event
        match = re.match(pattern, step)
        if match:
            date = match.group('date') if 'date' in match.groupdict() else None
            event = match.group('event') if 'event' in match.groupdict() else None
            if date and event:
                return True
    return False

def extract_steps_with_years_events(step_lines):
    years = []
    events = []
    for step_line in step_lines:
        # Split the step line by the colon to separate the step number and the rest
        step_parts = step_line.split(": ", 1)
        print(step_parts)
        if len(step_parts) < 2:
            continue  # Skip if the format is unexpected
        
        # Further split the second part by the dash to separate the year and event
        year_event = step_parts[1].split(" - ", 1)
        
        if len(year_event) < 2:
            continue  # Skip if the format is unexpected
        
        year = year_event[0].strip()  # Extract the year part
        event = year_event[1].strip()  # Extract the event part
        print(year)
        print(event)
        
        years.append((year))
        events.append(event)
    return years, events



# Function to create the plot and directly display it in Streamlit
def plot_large_timeline(sequence):
    years, events = extract_steps_with_years_events(list_steps(sequence)[0])

    if len(years) != len(events):
        raise ValueError("The length of 'years' and 'events' must be the same.")
    
    nvidia_green = "#76B900"
    nvidia_red = "#D22F27"
    dark_background = "#0B0B0B"
    
    fig, ax = plt.subplots(figsize=(38.4, 21.6), dpi=1200)

    ax.plot([0, len(years) - 1], [0, 0], color='gray', linewidth=3, alpha=0.6)

    colors = [nvidia_green] * len(years)

    ax.scatter(range(len(years)), [0] * len(years), color=colors, s=300, zorder=3, edgecolor=nvidia_red, linewidth=2)

    for i, (year, event) in enumerate(zip(years, events)):
        event = event.replace("**", "").strip()
        
        y_pos = 0.4 if i % 2 == 0 else -0.4
        # Event text (larger and more readable)
        ax.text(i, y_pos, event, ha='center', fontsize=16, fontweight='bold', color=nvidia_green, rotation=45, rotation_mode='anchor')
        # Year text (larger size as well)
        ax.text(i, y_pos - 0.2 if i % 2 == 0 else y_pos + 0.2, year, ha='center', fontsize=14, color='white')

    for i in range(len(years)):
        ax.plot([i, i], [0, 0.3 if i % 2 == 0 else -0.3], color='gray', linestyle='--', alpha=0.8)

    # Customizing the plot aesthetics for NVIDIA theme
    ax.set_ylim(-0.6, 0.6)  # More vertical space for labels
    ax.get_yaxis().set_visible(False)
    ax.set_xlim(-1, len(years))
    ax.set_title('Timeline Events Visualization', fontsize=28, fontweight='bold', color=nvidia_green)

    # Hide axes spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)

    # Set dark background for NVIDIA theme
    ax.set_facecolor(dark_background)
    fig.patch.set_facecolor(dark_background)

    # Display the high-resolution plot
    st.pyplot(fig)


def extract(step_lines):
    events = []
    for step_line in step_lines:
        step_parts = step_line.split(": ", 1)
        if len(step_parts) < 2:
            continue  # Skip if the format is unexpected
        
        # not a timeline event so the second part becomes the node
        events.append(step_parts[1])
    return events
def visualize_linked_list_with_heading(elements):
    # Generate steps for each element
    elements_with_steps = [f"Step {i + 1}: {element}" for i, element in enumerate(elements)]

    # HTML, CSS, and JavaScript code for the linked list visualization
    html_code = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Linked List Visualization</title>
        <style>
            body {{
                margin: 0;
                padding: 0;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: #0B0B0B; /* Dark background to contrast with container */
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }}

            .outer-container {{
                background: linear-gradient(135deg, #76B900, #0B0B0B);
                padding: 20px;
                border-radius: 30px; /* Rounded edges for the entire container */
                box-shadow: 0 10px 20px rgba(0, 0, 0, 0.5);
                display: flex;
                flex-direction: column;
                align-items: center;
                width: 95%;  /* Increased width to make it longer */
                max-height: 90%;
                overflow: hidden;
            }}

            .heading {{
                font-size: 36px;
                color: #ffffff;
                text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.4);
                margin-bottom: 30px;
                font-weight: bold;
                background-color: rgba(0, 0, 0, 0.2);
                padding: 10px 20px;
                border-radius: 10px;
            }}

            .linked-list {{
                display: flex;
                align-items: center;
                justify-content: center;
                flex-wrap: wrap;
                max-width: 100%;
                border-radius: 15px; /* Rounded edges for linked list container */
                padding: 20px; /* Added padding to spread out nodes a bit more */
            }}

            .node {{
                background-color: #76B900;
                color: white;
                padding: 15px 30px; /* Increased padding for larger nodes */
                margin: 15px;
                border-radius: 30px;
                position: relative;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-size: 18px;
                text-align: center;
                box-shadow: 0 8px 15px rgba(0, 0, 0, 0.2);
                transition: transform 0.3s ease;
            }}

            .node:hover {{
                transform: scale(1.1);
            }}

            .arrow {{
                width: 80px; /* Increased width for longer arrows */
                height: 4px;
                background-color: #D22F27; /* NVIDIA Red */
                margin: 10px;
                position: relative;
                border-radius: 15px; /* Rounded edges for the arrows */
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
            }}

            .arrow:after {{
                content: "";
                position: absolute;
                top: -6px;
                right: -12px;
                border-top: 10px solid transparent;
                border-left: 12px solid #D22F27;
                border-bottom: 10px solid transparent;
            }}

            /* Responsive behavior */
            @media (max-width: 600px) {{
                .node {{
                    font-size: 14px;
                    padding: 10px 12px;
                }}

                .arrow {{
                    width: 50px; /* Reduced width for smaller screens */
                }}
            }}
        </style>
    </head>
    <body>
        <div class="outer-container">
            <div class="heading">Visualization for Reconstruction</div>
            <div class="linked-list" id="linked-list"></div>
        </div>

        <script>
            // Function to generate the linked list dynamically with steps
            function generateLinkedList(elements) {{
                const linkedListContainer = document.getElementById('linked-list');
                linkedListContainer.innerHTML = '';  // Clear previous content

                elements.forEach((element, index) => {{
                    // Create a new node
                    const node = document.createElement('div');
                    node.classList.add('node');
                    node.innerText = element;

                    // Add the node to the linked list container
                    linkedListContainer.appendChild(node);

                    // If it's not the last element, add an arrow between nodes
                    if (index < elements.length - 1) {{
                        const arrow = document.createElement('div');
                        arrow.classList.add('arrow');
                        linkedListContainer.appendChild(arrow);
                    }}
                }});
            }}

            // Passing the Python list into the JavaScript function
            const elements = {elements_with_steps};
            generateLinkedList(elements);
        </script>
    </body>
    </html>
    """

    # Inject the HTML, CSS, and JavaScript into Streamlit
    st.components.v1.html(html_code, height=600)


def call_visualisation(sequence):
    if (list_steps(sequence)[1]) == "timeline":
        plot_large_timeline(sequence)
    else:
        visualize_linked_list_with_heading(extract(list_steps(sequence)[0]))

