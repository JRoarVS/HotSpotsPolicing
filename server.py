from model import *
from agent import *

from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import ChartModule
from mesa.visualization.UserParam import UserSettableParameter


#set parameters
set_height = 103
set_width = 100
n_cops = 13
n_agents = 300

# Design the agent portrayal
def agent_portrayal(agent):
    portrayal = {
        "Filled": "true",
        "r": 0.5} 
    
    if agent.typ == "building":
        if agent.risk > 0 and agent.model.show_risky == True:
            portrayal["Shape"] = "rect"
            portrayal["Color"] = "#4A235A"
            portrayal["Layer"] = 0
            portrayal["w"] = 1
            portrayal["h"] = 1
        else:
            portrayal["Shape"] = "rect"
            portrayal["Color"] = "#2ECC71"
            portrayal["Layer"] = 0
            portrayal["w"] = 1
            portrayal["h"] = 1
        
    elif agent.typ == "road":
        if agent.model.see_crime == True: # Only works if checkbox for showing crims is True.
            if agent.crime_incidents > 5:
                portrayal["Shape"] = "rect"
                portrayal["Color"] = "#34495E"
                portrayal["Layer"] = 1
                portrayal["w"] = 1
                portrayal["h"] = 1
            elif 3 > agent.crime_incidents > 0:
                portrayal["Shape"] = "rect"
                portrayal["Color"] = "#839192" 
                portrayal["Layer"] = 1
                portrayal["w"] = 1
                portrayal["h"] = 1
            elif 5 > agent.crime_incidents > 3:
                portrayal["Shape"] = "rect"
                portrayal["Color"] = "#7F8C8" 
                portrayal["Layer"] = 1
                portrayal["w"] = 1
                portrayal["h"] = 1
            else:            
                portrayal["Shape"] = "rect"
                portrayal["Color"] = "#CACFD2" 
                portrayal["Layer"] = 1
                portrayal["w"] = 1
                portrayal["h"] = 1    
        elif agent.model.show_zones == True: # Only works if checkbox for showing zones is True.
            if agent.grid_nr == 1:            
                portrayal["Shape"] = "rect"
                portrayal["Color"] = "black" 
                portrayal["Layer"] = 1
                portrayal["w"] = 1
                portrayal["h"] = 1
            elif agent.grid_nr == 2:
                portrayal["Shape"] = "rect"
                portrayal["Color"] = "#1B4F72" 
                portrayal["Layer"] = 1
                portrayal["w"] = 1
                portrayal["h"] = 1
            elif agent.grid_nr == 3:
                portrayal["Shape"] = "rect"
                portrayal["Color"] = "#6C3483" 
                portrayal["Layer"] = 1
                portrayal["w"] = 1
                portrayal["h"] = 1                     
            elif agent.grid_nr == 4:
                portrayal["Shape"] = "rect"
                portrayal["Color"] = "#7D6608" 
                portrayal["Layer"] = 1
                portrayal["w"] = 1
                portrayal["h"] = 1
        else:
            portrayal["Shape"] = "rect"
            portrayal["Color"] = "#CACFD2" 
            portrayal["Layer"] = 1
            portrayal["w"] = 1
            portrayal["h"] = 1                    

    elif agent.typ == "civilian":
        if agent.chronic_offender == True:
            portrayal["Shape"] = "circle"
            portrayal["Color"] = "red"
            portrayal["Layer"] = 2
            portrayal["r"] = 1
        elif agent.chronic_offender == False and agent.criminal_propensity > 0:
            portrayal["Shape"] = "circle"
            portrayal["Color"] = "#B12702"
            portrayal["Layer"] = 2
            portrayal["r"] = 1
        else:
            portrayal["Shape"] = "circle"
            portrayal["Color"] = "#C2654C"
            portrayal["Layer"] = 2
            portrayal["r"] = 1
    elif agent.typ == "cop":
        if agent.hotspot_patrol:
            portrayal["Shape"] = "circle"
            portrayal["Color"] = "#5B2C6F"
            portrayal["Layer"] = 2
            portrayal["r"] = 1
        else:
            portrayal["Shape"] = "circle"
            portrayal["Color"] = "blue"
            portrayal["Layer"] = 2
            portrayal["r"] = 1
    return portrayal

# Create the grid with the agent design
grid = CanvasGrid(
    agent_portrayal, 
    set_width,
    set_height, 
    800,
    800)

# Chart for datacollection
chart = ChartModule([{"Label": "Victimised",
                      "Color": "Black"}],
                   data_collector_name="datacollector")

# Dictionary of user settable parameters - these map to the model __init__ parameters
model_params = {
    # Slider for adjusting number of hot spots police
    "N_strategic_cops": UserSettableParameter(param_type="slider",
    value= 10, 
    name="Percentage of Hot Spots Policing Patrols", 
    min_value= 0, 
    max_value= 100,
    step= 10, 
    description="Percentage of cops that are patrolling hotspots"
    ),
    # Show risky locations
    "show_risky": UserSettableParameter(param_type="checkbox",
     name="Show Risky Locations",
     value=False), 
     # Visualise crime events
    "see_crime": UserSettableParameter(param_type="checkbox",
     name="Show Crime Hot Spots",
     value=False),
    # Visualise zones
    "show_zones": UserSettableParameter(param_type="checkbox",
     name="Show the Four Zones",
     value=False), 
    "N": n_agents, 
    "NC": n_cops, 
    "width": set_width, 
    "height": set_height
}

# Set up the server
server = ModularServer(Map,
                       [grid, chart],
                       "Hot Spots Policing",
                       model_params
                       )

# Initiate the server
server.port = 8521 # The default
server.launch()
