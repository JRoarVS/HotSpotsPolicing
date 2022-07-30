from itertools import count
from random import choice
from mesa import Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from agent import Civilian, StreetPatch

# def count_civ(model):
#     agent_count = model.num_agents
#     return agent_count

def ethnic_count(model):
    black_count = [agent.ethnicity for agent in model.schedule.agents]
    return black_count


class Map(Model):
    """
    A model that simulates hot spots policing in a city and contains all the agents.
    """
    def __init__(self, N, width, height):
        self.num_agents = N
        self.grid = MultiGrid(width, height, torus=False)
        self.schedule = RandomActivation(self)
        self.running =  True

        # This creats the streetpatch agents
        for x_k in range(width):
            for y_k in range(height):
                '''creates an agent with unique ID'''
                i = 10000000 + (x_k * height) + y_k
                position = (x_k, y_k)
                s = StreetPatch(i, self, position)
                '''adds the agent to the scheduler'''
                #self.schedule.add(s)
                '''adds the agent to a grid cell'''
                self.grid.place_agent(s, position)

        exclude_x = list(range(0,100,3))
        exclude_y = list(range(0,120,6))       
        
        # This creates civilian agents
        for i_k in range(self.num_agents):
            # x = self.random.randrange(self.grid.width)
            # y = self.random.randrange(self.grid.height)
            x = choice([x_l for x_l in range(0, self.grid.width) if x_l not in exclude_x])
            y = choice([y_l for y_l in range(0, self.grid.width) if y_l not in exclude_y])
            position = (x,y)
            prev_position = (x,y)
            a = Civilian(i_k, self, position, prev_position)
            self.schedule.add(a)
            self.grid.place_agent(a, position)

        # Metric to measure the model
        self.datacollector = DataCollector(
            model_reporters={"Count": ethnic_count},
            agent_reporters={"Ethnicity": lambda x: x.ethnicity},
        )

    def step(self):
        """Runs a single tick of the clock in the simulation"""
        self.datacollector.collect(self)
        self.schedule.step()


        