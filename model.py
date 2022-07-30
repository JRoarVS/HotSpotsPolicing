from itertools import count
from pyexpat import model
from random import choice
from mesa import Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from agent import Civilian, StreetPatch

def count_civ(model):
    agent_count = model.num_agents
    return agent_count

# def ethnic_count(model):
#     black_count = [agent.ethnicity for agent in model.schedule.agents]
#     return black_count


class Map(Model):
    """
    A model that simulates hot spots policing in a city and contains all the agents.
    """
    def __init__(self, N, width, height):
        self.num_agents = N
        self.grid = MultiGrid(width, height, torus=False)
        self.schedule = RandomActivation(self)
        self.running =  True

        # This creats the streetpatch agents.
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
        
        # This creates civilian agents.
        for i_k in range(self.num_agents):
            position = self.random_activity_generator() 
            prev_position = self.random_activity_generator()
            moving = "moving" # Moving starts off as False because all agents start in their homes.
            destination = []
            timer = 0

            # Assign random activity nodes for the agents. This will be their routine activities.
            activity_nodes = []
            N_nodes = 4
            for activity in range(0,N_nodes):
                activity = self.random_activity_generator()
                activity_nodes.append(activity)         

            a = Civilian(i_k, self, position, prev_position, activity_nodes, moving, destination, timer)
            self.schedule.add(a)
            self.grid.place_agent(a, position)

        # Metric to measure the model.
        self.datacollector = DataCollector(
            model_reporters={
                "white": lambda m: self.count_ethnic_citizens(m, "white"),
                "black": lambda m: self.count_ethnic_citizens(m, "black"),
                "asian": lambda m: self.count_ethnic_citizens(m, "asian"),
                "other": lambda m: self.count_ethnic_citizens(m, "other")
            },
            agent_reporters={
                "x": lambda a: a.pos[0],
                "y": lambda a: a.pos[1]
            }
        )

    def random_activity_generator(self):
        # Creates exclusion list to identify spawnable patches.
        exclude_x = list(range(0,100,3))
        exclude_y = list(range(0,120,6))  
        #Pick random x and y coordinate that excludes roads.
        x = choice([x_l for x_l in range(0, self.grid.width) if x_l not in exclude_x])
        y = choice([y_l for y_l in range(0, self.grid.height) if y_l not in exclude_y])
        return (x,y)


    def step(self):
        '''
        Runs a single tick of the clock in the simulation
        '''
        self.datacollector.collect(self)
        self.schedule.step()

    @staticmethod
    def count_ethnic_citizens(model, ethnicity):
        '''
        Helper method to count agent ethnicity.
        '''
        ethnic_count = 0
        for agent in model.schedule.agents:
            if agent.typ == "civilian":
                if agent.ethnicity == ethnicity:
                    ethnic_count += 1
        return ethnic_count
