from model import *
from agent import *

from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import ChartModule

#set parameters
set_height = 103
set_width = 100
n_cops = 10
n_agents = 300

# Design the agent portrayal
def agent_portrayal(agent):
    portrayal = {
        "Filled": "true",
        "r": 0.5} 
    
    if agent.typ == 'building':
        portrayal["Shape"] = "rect"
        portrayal["Color"] = "beige"
        portrayal["Layer"] = 0
        portrayal["w"] = 1
        portrayal["h"] = 1
        
    elif agent.typ == 'road':
        portrayal["Shape"] = "rect"
        portrayal["Color"] = "gray" 
        portrayal["Layer"] = 0
        portrayal["w"] = 1
        portrayal["h"] = 1
        
    elif agent.typ == 'civilian':
        portrayal["Shape"] = "circle"
        portrayal["Color"] = "red"
        portrayal["Layer"] = 1
        portrayal["r"] = 1
    else:
        portrayal["Shape"] = "circle"
        portrayal["Color"] = "blue"
        portrayal["Layer"] = 1
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
chart = ChartModule([{"Label": "Count",
                      "Color": "Black"}],
                   data_collector_name='datacollector')

# Set up the server
server = ModularServer(Map,
                       [grid, chart],
                       "Hot Spots Policing",
                       {"N": n_agents, "NC": n_cops, "width": set_width, "height": set_height}
                       )

# Initiate the server
server.port = 8521 # The default
server.launch()
