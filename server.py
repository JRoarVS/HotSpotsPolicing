from model import *
from agent import *
import pandas as pd
from mesa import batchrunner
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.modules import ChartModule
from mesa.visualization.UserParam import UserSettableParameter
from mesa.visualization.ModularVisualization import ModularServer
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

#----------------------------------------
# Model parameters:
HEIGHT = 103
WIDTH = 100
N_COPS = 41 # 41
N_AGENTS = 11402 # 11402

# Data collection parameters:
COLLECT_DATA = MONTH
ITERATIONS = 1

# Option for how the model should run:
OPTION = 2 
#1 = visualisation
#2 = batch_run

if OPTION == 1: # Initiate the server through jupyter in browser to visualise.
    #----------------------------------------
    # Design the agent portrayal
    def agent_portrayal(agent):
        portrayal = {
            "Filled": "true",
            "r": 0.5} 
        
        if agent.typ == "building":
                portrayal["Shape"] = "rect"
                portrayal["Color"] = "#2ECC71"
                portrayal["Layer"] = 0
                portrayal["w"] = 1
                portrayal["h"] = 1
            
        elif agent.typ == "road":
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
        "N": N_AGENTS, 
        "NC": N_COPS, 
        "width": WIDTH, 
        "height": HEIGHT
    }

    model_run = Map(model_params["N"], 
    model_params["NC"], 
    model_params["width"], 
    model_params["height"], 
    model_params["N_strategic_cops"])

    done = False
    if __name__ == '__main__':
        freeze_support()
        results_batch = batchrunner.batch_run(
            Map,
            model_params,
            iterations = ITERATIONS, 
            number_processes= None,
            data_collection_period = COLLECT_DATA,
            display_progress= True
        )
        done = True

    if done == True:
        results_batch_df = pd.DataFrame(results_batch)
        results_batch_df = results_batch_df.loc[:, results_batch_df.columns.intersection([
        'iteration',
        'Step',
        'N_strategic_cops', 
        'Victimised', 
        'Stopped_Searched',
        'AgentID',
        'Ethnicity',
        'zone',
        'N_victimised',
        'N_stop_searched'])]
        results_batch_df = results_batch_df[results_batch_df['AgentID'] < 12000]
        results_batch_df.to_csv("simulation_data.csv")

        print(results_batch_df.keys())
        print(results_batch_df.tail())