from model import *
from agent import *

from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import ChartModule
from mesa.visualization.UserParam import UserSettableParameter
from mesa import batchrunner

import pandas as pd
from multiprocessing import freeze_support


#----------------------------------------
#GLOBAL PROCEDURES
def getdata_model(model):
    """A procedure that extracts model data from the datacollector"""
    result = model.datacollector.get_model_vars_dataframe()
    return result

def getdata_model(model):
    """A procedure that extracts agent data from the datacollector"""
    result = model.datacollector.get_agent_vars_dataframe()
    return result

#set parameters
HEIGHT = 103
WIDTH = 100
N_COPS = 41 # 41
N_AGENTS = 11402 # 11402

OPTION = 2

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
        if agent.model.see_crime == True: # Only works if checkbox for showing crime is True.
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
    WIDTH,
    HEIGHT, 
    800,
    800)

# Chart for datacollection
chart = ChartModule([{"Label": "Victimised",
                      "Color": "Black"}],
                   data_collector_name="datacollector")

if OPTION == 1: # Initiate the server through jupyter in browser to visualise.
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
        "N": N_AGENTS, 
        "NC": N_COPS, 
        "width": WIDTH, 
        "height": HEIGHT
    }

    # Set up the server
    server = ModularServer(Map,
                        [grid, chart],
                        "Hot Spots Policing",
                        model_params
                        )


    # Initiate the server through jupyter in browser to visualise.
    server.port = 8521 # The default
    server.launch()

elif OPTION == 2: # Collect data through batchrunner without visualisation:
        # Dictionary of user settable parameters - these map to the model __init__ parameters
    model_params = {
        # Slider for adjusting number of hot spots police
        "N_strategic_cops": 10,
        "show_risky": False,
        "see_crime": False,
        "show_zones": False, 
        "N": N_AGENTS, 
        "NC": N_COPS, 
        "width": WIDTH, 
        "height": HEIGHT
    }

    model_run = Map(model_params["N"], 
    model_params["NC"], 
    model_params["width"], 
    model_params["height"], 
    model_params["N_strategic_cops"], 
    model_params["show_risky"], 
    model_params["see_crime"], 
    model_params["show_zones"])

    if __name__ == '__main__':
        freeze_support()
    results_batch = batchrunner.batch_run(
        Map,
        model_params,
        iterations = 6,
        number_processes= None,
        data_collection_period = MONTH,
        display_progress= True
    )

    results_batch_df = pd.DataFrame(results_batch)
    results_batch_df.to_csv("robbery_rates.csv")

    print(results_batch_df.keys())
    print(results_batch_df.tail())