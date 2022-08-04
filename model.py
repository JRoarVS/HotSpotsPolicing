import numpy as np
import scipy.stats as sct
from mesa import Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from agent import Civilian, StreetPatch, Cop

def get_total_offences(model):
    """Returns the number of agents that have been a victim to street robbery."""
    agents = [a.N_victimised for a in model.schedule.agents if isinstance(a, Civilian)]
    return int(np.sum(agents))

class Map(Model):
    """
    A model that simulates hot spots policing in a city and contains all the agents.
    """
    def __init__(self, N, NC, width, height):
        self.num_agents = N
        self.num_cops = NC
        self.grid = MultiGrid(width, height, torus=False)
        self.schedule = RandomActivation(self)
        self.running =  True
        self.N_victims = 0

        # Initialise streetpatch agents.
        #----------------------------------------------------------------
        for x_k in range(width):
            for y_k in range(height):
                '''creates an agent with unique ID'''
                i = 10000000 + (x_k * height) + y_k
                position = (x_k, y_k)
                risk = self.truncated_poisson(0.19, 6, 1) # Draw a random number from a poisson distribution.
                crime_incidents = 0
                s = StreetPatch(i, self, position, risk, crime_incidents)
                '''adds the agent to the scheduler'''
                self.schedule.add(s)
                '''adds the agent to a grid cell'''
                self.grid.place_agent(s, position)     
        
        # Initialise civilian agents.
        #----------------------------------------------------------------
        criminal_propensity_rate = 0.0925 # Rate of agents who have a criminal propensity rate greater than 0.
        chronic_offender_rate = 0.05 # Of those with criminal propensity, 5% have a chronic score (propensity = 10).
        
        # Offender values
        criminal_total = round(self.num_agents * criminal_propensity_rate) # Number of agents with criminal propensity greater than 0.
        chronic_criminal = round(criminal_total * chronic_offender_rate) # Number of chronic offenders.
        criminal_non_chronic = round(self.num_agents * criminal_propensity_rate - chronic_criminal) # Number of non-chronic agents with greater criminal propensity than 0.

        # Ethnicity values
        white_perc = 0.449
        other_perc = 0.233
        asian_perc = 0.185
        black_perc = 0.133

        white_pop = self.num_agents * white_perc
        other_pop = self.num_agents * other_perc
        asian_pop = self.num_agents * asian_perc
        black_pop = self.num_agents * black_perc

        for i_k in range(self.num_agents):
            position = self.random_activity_generator() 
            prev_position = self.random_activity_generator()
            moving = "moving"
            destination = []
            timer = 0
            travel_speed = np.random.uniform(6,9)
            N_victimised = 0

            # Parameters for creating random distribution
            lower = 1
            upper = 11
            mu = 5.5
            sigma = 1.2
            N = 1
            attractiveness = sct.truncnorm.rvs(
                    (lower-mu)/sigma,(upper-mu)/sigma,loc=mu,scale=sigma,size=N)
            perceived_guardianship = sct.truncnorm.rvs(
                    (lower-mu)/sigma,(upper-mu)/sigma,loc=mu,scale=sigma,size=N)
            perceived_capability = np.random.uniform(-5,6) # random number between -5 and 5.

            # Assign criminal propensity rates to all agents. 
            if criminal_non_chronic > 0:
                criminal_propensity = self.random.choice(range(6,10,1)) # Propensity score between 6 and 9
                criminal_non_chronic -= 1
                chronic_offender = False
                time_to_offending = np.random.uniform(0,43200)
                victimisation = 0 # Will not be used
            elif chronic_criminal > 0:
                criminal_propensity = 10 # Propensity score of 10
                chronic_criminal -= 1
                chronic_offender = True
                time_to_offending = 0
                victimisation = 0 # Will not be used
            else:
                criminal_propensity = 0 # Propensity score of 0
                chronic_offender = False
                time_to_offending = 0 # Not applicable to law-abiding citizens.
                victimisation = 20


            # Assign random activity nodes for the agents. This will be their routine activities.
            activity_nodes = []
            N_nodes = 4
            for activity in range(0,N_nodes):
                activity = self.random_activity_generator()
                activity_nodes.append(activity)  

            # Assign ethnicities to the population
            if white_pop > 0:
                white_pop -= 1
                ethnicity = 'white'
            elif other_pop > 0:
                other_pop -= 1
                ethnicity = 'other'
            elif asian_pop > 0:
                asian_pop -= 1
                ethnicity = 'asian'
            elif black_pop > 0:
                black_pop -= 1
                ethnicity = 'black'            

            a = Civilian(i_k, 
            self, 
            position, 
            prev_position, 
            activity_nodes, 
            moving, 
            destination, 
            timer, 
            criminal_propensity,
            chronic_offender,
            travel_speed,
            time_to_offending,
            victimisation,
            attractiveness,
            perceived_guardianship,
            perceived_capability,
            N_victimised,
            ethnicity)
            self.schedule.add(a)
            self.grid.place_agent(a, position)

        # Initialise cop agents.
        #----------------------------------------------------------------
        for j_k in range(self.num_cops):
            cop_id = j_k + 10000000000
            position = self.random_patrol_node_generator() 
            prev_position = position
            moving = "moving" 
            timer = 0
            travel_speed = np.random.uniform(6,9)
            hotspot_patrol = True

            # Assign random 1 random activity node. This will change everytime the cop arrives at the node.
            patrol_node = self.random_patrol_node_generator()
            destination = patrol_node
            b = Cop(cop_id, 
            self, 
            position, 
            prev_position,
            patrol_node, 
            moving, 
            destination, 
            timer,
            travel_speed,
            hotspot_patrol)
            self.schedule.add(b)
            self.grid.place_agent(b, position)

        # Metric to measure the model.
        #----------------------------------------------------------------
        self.datacollector = DataCollector(
            model_reporters={
                "Victimised": get_total_offences
                },
            agent_reporters={
                "Position": "pos"
            }
        )

    def random_activity_generator(self):
        """
        Creates a random node for the agent which will serve as the civilians' home.
        """
        list_of_roads = []
        for i in self.schedule.agents:
            if i.typ == 'building':
                list_of_roads.append(i.pos)
        
        xy = self.random.choice(list_of_roads)

        return (xy) 
    
    def random_patrol_node_generator(self):
        """
        Create a random node on the road map where the cop agent will move to.
        """
        all_agents = self.schedule.agents
        roads = [obj for obj in all_agents if isinstance(obj, StreetPatch)]
        list_of_roads = []
        for i in roads:
            if i.typ == 'road':
                list_of_roads.append(i.pos)
        
        xy = self.random.choice(list_of_roads)

        return (xy)   

    def step(self):
        """
        Runs a single tick of the clock in the simulation
        """
        self.datacollector.collect(self)
        self.schedule.step()
        self.finished()
    
    def finished(self):
        N_ticks = 0
        if N_ticks == 10:
            self.running = False
        else:
            N_ticks += 1

    def truncated_poisson(self, mu, max_value, size):
        """
        Returns a random number based on a poisson distribution.
        """
        temp_size = size
        while True:
            temp_size *= 2
            temp = sct.poisson.rvs(mu, size=temp_size)
            truncated = temp[temp <= max_value]
            if len(truncated) >= size:
                return truncated[:size]

    @staticmethod
    def count_ethnic_citizens(model, ethnicity):
        """
        Helper method to count agent ethnicity.
        """
        ethnic_count = 0
        for agent in model.schedule.agents:
            if agent.typ == "civilian":
                if agent.ethnicity == ethnicity:
                    ethnic_count += 1
        return ethnic_count
