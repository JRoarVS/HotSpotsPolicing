import numpy as np
import scipy.stats as sct
from mesa import Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from agent import Civilian, StreetPatch, Cop

# GLOBAL PROCEDURES:
#--------------------------------------------------------------------------
def get_total_offences(model):
    """Returns the number of agents that have been a victim to street robbery."""
    agents = [a.N_victimised for a in model.schedule.agents if isinstance(a, Civilian)]
    return int(np.sum(agents))

def get_N_stopsearch(model):
    """Returns the number of agents that have been stopped and search"""
    agents = [a.stop_searched for a in model.schedule.agents if isinstance(a, Civilian)]
    return int(np.sum(agents))

def get_ethnicity(agent):
    """Returns the ethnicity of the agent"""
    if isinstance(agent, Civilian):
        ethnic = agent.ethnicity
    else:
        ethnic = "NA"
    return ethnic


# def get_offend_score(agent):
#     """Returns the offend score of an civilian agent"""
#     if isinstance(agent, Civilian):
#         offend = agent.offend_score
#     else:
#         offend = "NA"
#     return offend

# def get_stop_search_score(agent):
#     """Returns the offend score of a cop agent"""
#     if isinstance(agent, Cop):
#         stopsearch = agent.stopsearch_score
#     else:
#         stopsearch = "NA"
#     return stopsearch


# GLOBAL VARIABLES:
#--------------------------------------------------------------------------
# Offending variables:
CRIMINAL_PROPENSITY_RATE = 0.0925 # Rate of agents who have a criminal propensity rate greater than 0.
CHRONIC_OFFENDER_RATE = 0.05 # Of those with criminal propensity, 5% have a chronic score (propensity = 10).

# Ethnicity values:
WHITE_PERC = 0.449
OTHER_PERC = 0.233
ASIAN_PERC = 0.185
BLACK_PERC = 0.133

# Time values:
MONTH = 43200
YEAR = 518400

class Map(Model):
    """
    A model that simulates hot spots policing in a city and contains all the agents.
    """
    def __init__(self, N, NC, width, height, N_strategic_cops):
        self.num_agents = N
        self.num_cops = NC
        self.grid = MultiGrid(width, height, torus=False)
        self.schedule = RandomActivation(self)
        self.running =  True
        self.N_victims = 0
        self.N_ticks = 0
        # Visualisation:
        self.N_strategic_cops = N_strategic_cops # Slider: Adjust the percentage of strategic cops.

        # Initialise streetpatch agents.
        #----------------------------------------------------------------
        for x_k in range(width):
            for y_k in range(height):
                """creates an agent with unique ID"""
                i = 300000 + (x_k * height) + y_k
                position = (x_k, y_k)
                risk = self.truncated_poisson(0.19, 6, 1) # Draw a random number from a poisson distribution.
                crime_incidents = 0

                # Create grid number for each section of the map
                if y_k > 51 and x_k < 50:
                    grid_nr = 1
                elif y_k > 51 and x_k >= 50:
                    grid_nr = 2
                elif y_k <= 51 and x_k < 50:
                    grid_nr = 3
                elif y_k <= 51 and x_k >= 50:
                    grid_nr = 4

                s = StreetPatch(i, self, position, risk, crime_incidents, grid_nr)
                """adds the agent to the scheduler"""
                self.schedule.add(s)
                """adds the agent to a grid cell"""
                self.grid.place_agent(s, position)     
        
        # Initialise civilian agents.
        #----------------------------------------------------------------
        criminal_propensity_rate = CRIMINAL_PROPENSITY_RATE
        chronic_offender_rate = CHRONIC_OFFENDER_RATE
        
        # Offender values
        criminal_total = round(self.num_agents * criminal_propensity_rate) # Number of agents with criminal propensity greater than 0.
        chronic_criminal = round(criminal_total * chronic_offender_rate) # Number of chronic offenders.
        criminal_non_chronic = round(self.num_agents * criminal_propensity_rate - chronic_criminal) # Number of non-chronic agents with greater criminal propensity than 0.

        white_pop = self.num_agents * WHITE_PERC
        other_pop = self.num_agents * OTHER_PERC
        asian_pop = self.num_agents * ASIAN_PERC
        black_pop = self.num_agents * BLACK_PERC

        # Set up zone values:
        zone_1 = (self.num_agents/4)-(criminal_total/4)
        zone_2 = (self.num_agents/4)-(criminal_total/4)
        zone_3 = (self.num_agents/4)-(criminal_total/4)

        for i_k in range(self.num_agents):
            moving = "moving"
            destination = []
            timer = 0
            travel_speed = np.random.uniform(6,9)
            N_victimised = 0
            stop_searched = 0
            attractiveness = self.random_distribution()
            perceived_guardianship = self.random_distribution()
            perceived_capability = np.random.uniform(-5,6) # random number between -5 and 5.

            # Assign criminal propensity rates to all agents. 
            if criminal_non_chronic > 0:
                criminal_propensity = self.random.choice(range(6,10,1)) # Propensity score between 6 and 9
                criminal_non_chronic -= 1
                chronic_offender = False
                time_to_offending = np.random.uniform(0,43200)
                victimisation = 0 # Will not be used
                zone = self.random.choice(range(1,5)) # Give the offender a random grid cell
            elif chronic_criminal > 0:
                criminal_propensity = 10 # Propensity score of 10
                chronic_criminal -= 1
                chronic_offender = True
                time_to_offending = 0
                victimisation = 0 # Will not be used
                zone = self.random.choice(range(1,5)) # Give the offender a random grid cell
            else:
                criminal_propensity = 0 # Propensity score of 0
                chronic_offender = False
                time_to_offending = 0 # Not applicable to law-abiding citizens.
                victimisation = 20
                # Assign zones to civilians with no criminal propensity:
                if zone_1 > 0:
                    zone = 1
                    zone_1 -= 1
                elif zone_2 > 0:
                    zone = 2
                    zone_2 -= 1
                elif zone_3 > 0:
                    zone = 3
                    zone_3 -= 1
                else:
                    zone = 4

            list_of_nodes = self.random_activity_generator(zone) 
            list_of_risky_nodes = self.risky_activity_generator(zone)
            position = list_of_nodes[0]
            prev_position = list_of_nodes[0]

            # Assign random activity nodes for the agents. This will be their routine activities.
            activity_nodes = []
            activity_nodes.append(list_of_nodes[1])
            activity_nodes.append(list_of_nodes[2])
            activity_nodes.append(list_of_risky_nodes[0])
            activity_nodes.append(list_of_risky_nodes[1])
            
            # # Assign ethnicities to the population - Ethnic diversity in zone 1 and only whites in the other zones.
            # if white_pop > 0:
            #     white_pop -= 1
            #     ethnicity = "white"
            # elif other_pop > 0:
            #     other_pop -= 1
            #     ethnicity = "other"
            # elif asian_pop > 0:
            #     asian_pop -= 1
            #     ethnicity = "asian"
            # elif black_pop > 0:
            #     black_pop -= 1
            #     ethnicity = "black"    

            # Assign ethnicities to the population - Uniform distribution
            list_of_possible_ethn = []
            pops = [white_pop, other_pop, asian_pop, black_pop]
            for i in pops:
                if i > 0:
                    if i == white_pop:
                        list_of_possible_ethn.append("white")
                    elif i == other_pop:
                        list_of_possible_ethn.append("other")     
                    elif asian_pop > 0:
                        list_of_possible_ethn.append("asian")
                    elif black_pop > 0:
                        list_of_possible_ethn.append("black")
            
            random_float = self.random.uniform(0, 100)
            if random_float < 44.9 and "white" in list_of_possible_ethn:
                ethnicity = "white"
            elif 44.9 < random_float < 68.2 and "other" in list_of_possible_ethn:
                ethnicity = "other"
            elif 68.2 < random_float < 86.7 and "asian" in list_of_possible_ethn:
                ethnicity = "asian"
            else:
                ethnicity = "black"

            #ethnicity = self.random.choice(list_of_possible_ethn)
            if ethnicity == "white":
                white_pop -= 1
            elif ethnicity == "other":
                other_pop -= 1     
            elif ethnicity == "asian":
                asian_pop -= 1
            elif ethnicity == "black":
                black_pop -= 1     

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
            ethnicity,
            zone,
            stop_searched)
            self.schedule.add(a)
            self.grid.place_agent(a, position)

        # Initialise cop agents.
        #----------------------------------------------------------------
        # Cop values:
        nr_of_officers = round(self.num_cops * (self.N_strategic_cops / 100)) # Only strategic
        patrol_1 = (self.num_cops/4) - (nr_of_officers/4)
        patrol_2 = (self.num_cops/4) - (nr_of_officers/4)
        patrol_3 = (self.num_cops/4) - (nr_of_officers/4)

        for j_k in range(self.num_cops):
            cop_id = j_k + 20000000
            prev_position = position
            moving = "moving" 
            timer = 0
            travel_speed = np.random.uniform(6,9)

            if nr_of_officers > 0:
                nr_of_officers -= 1
                hotspot_patrol = True
                patrol_area = 1 # Starts at grid 1, but will move across the whole map.
            else:
                hotspot_patrol = False    
                # Create patrol areas for the cop agents
                if patrol_1 > 0:
                    patrol_area = 1
                    patrol_1 -= 1
                elif patrol_2 > 0:
                    patrol_area = 2
                    patrol_2 -= 1
                elif patrol_3 > 0:
                    patrol_3 -= 1
                    patrol_area = 3
                else:
                    patrol_area = 4
            
            position = self.random_patrol_node_generator(patrol_area) 

            # Assign random 1 random activity node. This will change everytime the cop arrives at the node.
            patrol_node = self.random_patrol_node_generator(patrol_area)
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
            hotspot_patrol,
            patrol_area)
            self.schedule.add(b)
            self.grid.place_agent(b, position)

        # Metric to measure the model.
        #----------------------------------------------------------------
        self.datacollector = DataCollector(
            model_reporters={
                "Victimised": get_total_offences,
                "Stopped_Searched": get_N_stopsearch,
                },
            agent_reporters={
                "Ethnicity": lambda a: getattr(a, "ethnicity", None),
                "zone": lambda a: getattr(a, "zone", None),
                "N_victimised": lambda a: getattr(a, "N_victimised", None),
                "N_stop_searched": lambda a: getattr(a, "stop_searched", None),
            }
        )

    def random_distribution(self):
        lower = 1
        upper = 11
        mu = 5.5
        sigma = 1.2
        N = 1

        random_distr = sct.truncnorm.rvs(
            (lower-mu)/sigma,(upper-mu)/sigma,loc=mu,scale=sigma,size=N)
        
        return random_distr

    def random_activity_generator(self, zone):
        """
        Creates a random node for the agent which will serve as the civilians' home and activity nodes.
        """
        list_of_roads = []
        list_of_output = []
        for i in self.schedule.agents:
            if i.typ == "building" and i.grid_nr == zone:
                list_of_roads.append(i.pos)
        
        for _ in range(3):
            selection = self.random.choice(list_of_roads)
            list_of_output.append(selection)

        return list_of_output 
    
    def risky_activity_generator(self, zone):
        """
        Selects random nodes that are risky (risk > 0)
        """
        list_of_risky_roads = []
        list_of_output = []
        for i in self.schedule.agents:
            if i.typ == "building" and i.grid_nr == zone and i.risk > 0:
                list_of_risky_roads.append(i.pos)
        for _ in range(2):
            selection = self.random.choice(list_of_risky_roads)
            list_of_output.append(selection)
        
        return(list_of_output)
    
    def random_patrol_node_generator(self, patrol_area):
        """
        Create a random node on the road map where the cop agent will move to.
        """
        grid_zone = patrol_area
        roads = [obj for obj in self.schedule.agents if isinstance(obj, StreetPatch)]
        list_of_roads = []
        for i in roads:
            if i.typ == "road" and i.grid_nr == grid_zone:
                list_of_roads.append(i.pos)
        
        xy = self.random.choice(list_of_roads)

        return (xy)

    def step(self):
        """
        Runs a single tick of the clock in the simulation.
        """
        self.datacollector.collect(self)
        self.schedule.step()
        self.finished()
    
    def finished(self):
        """
        Check if the model has reached its limit and then stop the simulation.
        """
        if self.N_ticks == MONTH:
            self.running = False
        else:
            self.N_ticks += 1

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
