from random import randint
from mesa import Agent
from numpy import random
import operator
from operator import attrgetter

# GLOBAL VARIABLES:
#--------------------------------------------------------------------------
# Stop and search values:
WHITE_STOP = 4
OTHER_STOP = 3
ASIAN_STOP = 3.6
BLACK_STOP = 4.4

# WHITE_STOP = 5.734 # 11.2341667
# OTHER_STOP = 5.585 # 11.085
# ASIAN_STOP = 5.4625 # 10.9625
# BLACK_STOP = 5.425 # 10.925

WHITE_THRESHOLD = 11.2341667
OTHER_THRESHOLD = 11.085
ASIAN_THRESHOLD = 10.9625
BLACK_THRESHOLD = 10.925

# Threshold rates:
ROBBERY_RATE = 14.753 # 14.75 produces an average of 39 robberies per month
STOP_SEARCH_RATE = 10.91  # 10.91 produces an average of  22 stop and searches per month


#----------------------------------------------------------------
class StreetPatch(Agent):
    """An agent that will be a patch in the map"""

    def __init__(self, unique_id, model, position, risk, crime_incidents, grid_nr):
        """
        Initialises the agent instance.
        """
        super().__init__(unique_id, model)

        # Create a list of x and y cor to generate a grid layout.
        roads_xcor = list(range(0,400,3))
        roads_ycor = list(range(0,400,6))
        self.pos = position
        self.risk = risk
        self.crime_incidents = crime_incidents
        self.grid_nr = grid_nr

        if(self.pos[0] in roads_xcor) or (self.pos[1] in roads_ycor):
            self.typ = "road"
        else:
            self.typ = "building"

    def step(self):
        return       

#----------------------------------------------------------------
class Civilian(Agent):
    """
    A member of the general population, which can either be a victim of street robbery or be the one committing it.
    """
    def __init__(self, 
    unique_id, 
    model, 
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
    stop_searched):
        super().__init__(unique_id, model)
        self.pos = position
        self.typ = "civilian"
        self.ethnicity = ethnicity  
        # Agent movement:
        self.home = position
        self.prev_pos = prev_position
        self.activity_nodes = activity_nodes
        self.moving = moving
        self.destination = destination
        self.timer = timer
        self.travel_speed = travel_speed
        # Offender parameters:
        self.criminal_propensity = criminal_propensity
        self.chronic_offender = chronic_offender
        self.time_to_offending = time_to_offending
        # Victimisation parameters:
        self.victimisation = victimisation
        self.attractiveness = attractiveness
        self.perceived_guardianship = perceived_guardianship
        self.perceived_capability = perceived_capability
        self.N_victimised = N_victimised
        self.zone = zone
        self.stop_searched = stop_searched
        self.offend_score = 0

    def move(self):
        """
        Inspect neighbours and move to the next cell towards the destination patch. 
        """
        if self.moving == "moving":
            if self.pos == self.home:
                self.destination = self.random.choice(self.activity_nodes) # Selects a new destination
            elif self.pos == self.destination:
                if randint(0,100) <= 79: # 80% chance of returning home
                    self.destination = self.home
                else:
                    # 20% chance of selecting any other activity node
                    self.destination = self.random.choice([a_node for a_node in self.activity_nodes if a_node not in self.pos])
            # Create list of possible neighbouring cells to move to. 
            self.update_neighbors()
            road_neighbours = []
            for agent in self.neighbors:
                if agent.pos == self.destination:
                    self.model.grid.move_agent(self, self.destination) # Do nothing if the agent is at an activity node. 
                else:
                    if agent.typ == "road": 
                        road_neighbours.append(agent.pos)

            # Check if agent has arrived. If agent has arrived at destination: set moving to "arrived". 
            if self.destination == self.pos and self.moving == "moving":  
                self.moving = "arrived"

            else:
                # Creating empty lists for directing the agents.
                right_dir = []
                wrong_dir = []

                # Create a list of right directions and wrong directions.
                distance = tuple(map(operator.sub, self.destination, self.pos))
                for coordinate in road_neighbours:
                    if coordinate != self.prev_pos:
                        next_distance = tuple(map(operator.sub, self.destination, coordinate))
                        if ((abs(next_distance[0]) < abs(distance[0])) or (abs(next_distance[1]) < abs(distance[1]))):
                            right_dir.append(coordinate)
                        else:
                            wrong_dir.append(coordinate)
                
                # Move to the right direction unless there is no right direction.
                if len(right_dir) > 0:
                    new_position = right_dir[0]
                else:
                    new_position = self.random.choice(wrong_dir)

                self.prev_pos = self.pos
                self.model.grid.move_agent(self, new_position)

        elif self.moving == "arrived":
            self.prev_pos = self.pos
            self.moving = "waiting"
            if self.pos == self.home:
                self.timer = 1 + int(random.uniform(0, 600)) # Home Node = 1 tick + U(0, 600)
            else:
                self.timer = 15 + int(random.uniform(0,480)) # Activity Node = 15 ticks + U(0, 480)
        else:   
            if self.timer == 0:
                self.moving = "moving"

    def offend(self):
        """
        Check if a suitable victim is in the same cell.
        """
        if self.criminal_propensity > 0 and self.moving == "moving" and self.time_to_offending >= 0:
            # Get information about agents on the same cell.
            same_cell = self.model.grid.get_cell_list_contents(self.pos)
            # Only select agents that are civilians
            filtered_cell = []
            for agent in same_cell:
                if agent.typ == "civilian":
                    filtered_cell.append(agent)
            the_offender = [self]

            if len(filtered_cell) > 1:
                victim = self.random.choice([i for i in filtered_cell if i not in the_offender])
                if self.cop_nearby() == False:
                    road_risk = 10 # Road risk can't be 10 
                    for f in same_cell:
                        if f.typ == "road":
                            road_risk = f.risk
                    if road_risk < 10:
                        Nc = (len(filtered_cell) - 2) + victim.perceived_guardianship
                        guardianship = self.perceived_capability + Nc 
                        rational_choice_score = victim.attractiveness - guardianship + self.criminal_propensity + road_risk
                        self.offend_score = rational_choice_score
                        if rational_choice_score >= ROBBERY_RATE:
                            victim.N_victimised += 1
                            if self.criminal_propensity < 20:
                                self.time_to_offending = self.time_to_offending_again()
                                neighbours = self.model.grid.get_neighborhood(
                                self.pos, moore=False, include_center = True, radius=2)                                 
                                whos_here = self.model.grid.get_cell_list_contents(neighbours)
                                for road in whos_here:
                                    if road.typ == "road":
                                        road.crime_incidents += 1
                    return
                return

    def cop_nearby(self):
        """
        Looks around to see if cops are nearby.
        """
        vision = 7
        cops_here = []
        neighbours = self.model.grid.get_neighborhood(
            self.pos, moore=False, radius=vision
        )
        whos_here = self.model.grid.get_cell_list_contents(neighbours)
        for i in whos_here:
            if i.typ == "cop":
                cops_here.append(i)

        if len(cops_here) > 0:
            return True # Cops nearby
        else:
            return False # No cops nearby

    def update_neighbors(self):
        """
        Look around and identify the neighbours.
        """
        self.neighborhood = self.model.grid.get_neighborhood(
            self.pos, moore=False, radius=1
        )
        self.neighbors = self.model.grid.get_cell_list_contents(self.neighborhood)

    def step(self):
        """
        A single tick in the simulation. 
        One tick equals to one minute and the agent can move between 6 and 8 steps per tick. 
        """
        if self.moving == "waiting":
            self.timer -= 1 # Countdown timer

        run_times = self.travel_speed
        if run_times > 0:
            while run_times > 0:
                run_times -= 1
                self.move()
                        
        # Calculate if a civilian will offend.
        self.offend()
        if 0 < self.criminal_propensity < 10:
            self.time_to_offending -= 1

    def time_to_offending_again(self):
        """
        Returns the number of ticks before agent can offend again.
        """
        time_offend = round(random.uniform(0, 43200)) # 0 to 30 days.
        return time_offend

#----------------------------------------------------------------
class Cop(Agent):
    """
    A police agent that will patrol the map and reacts to crime.
    """
    def __init__(self, 
    unique_id, 
    model, 
    position, 
    prev_position, 
    patrol_node, 
    moving, 
    destination, 
    timer,
    travel_speed,
    hotspot_patrol,
    patrol_area
    ):
        super().__init__(unique_id, model)
        self.pos = position
        self.typ = "cop"     
        # Agent movement:
        self.home = position
        self.prev_pos = prev_position
        self.patrol_node = patrol_node
        self.moving = moving
        self.destination = destination
        self.timer = timer
        self.travel_speed = travel_speed
        self.hotspot_patrol = hotspot_patrol
        self.patrol_area = patrol_area
        self.stopsearch_score = 0
        self.time_at_hotspot = 0 # Time spent at hot spots is 15 mins (15 ticks)

    def move(self):
        """
        Inspect neighbours and move to the next cell towards the destination patch. 
        """
        if self.moving == "moving":
            if self.pos == self.destination:
                if self.hotspot_patrol:
                    if self.time_at_hotspot == 0:
                        self.destination = self.hotspot_node_generator()
                        self.time_at_hotspot = 15
                else:
                    self.destination = self.random_patrol_node_generator()
            # Create list of possible neighbouring cells to move to. 
            self.update_neighbors()
            road_neighbours = []
            for agent in self.neighbors:
                if agent.pos == self.destination:
                    self.model.grid.move_agent(self, self.destination) # Do nothing.  
                else:
                    if agent.typ == "road": 
                        road_neighbours.append(agent.pos)

            # Check if agent has arrived. If agent has arrived at destination: set moving to "arrived". 
            if self.destination == self.pos and self.moving == "moving":
                if self.hotspot_patrol == True: 
                    self.moving = "at_the_scene"
                elif self.hotspot_patrol == False:  
                    self.moving = "arrived"      

            else:
                # Creating empty lists for directing the agents.
                right_dir = []
                wrong_dir = []

                distance = tuple(map(operator.sub, self.destination, self.pos))
                for coordinate in road_neighbours:
                    if coordinate != self.prev_pos:
                        next_distance = tuple(map(operator.sub, self.destination, coordinate))
                        if ((abs(next_distance[0]) < abs(distance[0])) or (abs(next_distance[1]) < abs(distance[1]))):
                            right_dir.append(coordinate)
                        else:
                            wrong_dir.append(coordinate)
                
                # Move to the right direction unless there is no right direction.
                if len(right_dir) > 0:
                    new_position = right_dir[0]
                else:
                    new_position = self.random.choice(wrong_dir)

                self.prev_pos = self.pos
                self.model.grid.move_agent(self, new_position)
        
        elif self.moving == "arrived":
            self.prev_pos = self.pos # Reset prev_pos
            self.moving = "moving"
        
        elif self.moving == "at_the_scene":
            if self.time_at_hotspot == 0:
                self.moving = "moving"


    def update_neighbors(self):
        """
        Look around and identify the neighbours.
        """
        self.neighborhood = self.model.grid.get_neighborhood(
            self.pos, moore=False, radius=1
        )
        self.neighbors = self.model.grid.get_cell_list_contents(self.neighborhood)
    
    def random_patrol_node_generator(self):
        """
        Gives a random patrol node to a cop agent.
        """       
        roads = [obj for obj in self.model.schedule.agents if isinstance(obj, StreetPatch)]
        list_of_roads = []
        for i in roads:
            if i.typ == "road" and i.grid_nr == self.patrol_area:
                list_of_roads.append(i.pos) 
        
        xy = self.random.choice(list_of_roads)

        return (xy)

    def hotspot_node_generator(self):
        """
        Gives a hotspot node to a cop agent.
        """       
        hotspots_values = []
        hotspots = []
        roads = [obj for obj in self.model.schedule.agents if isinstance(obj, StreetPatch)]

        # Create a list of the top five crime hot spots.
        for _ in range(5):
            hotspot_incidents = max(roads, key=attrgetter("crime_incidents")) # Get the max hot spots
             
            if hotspot_incidents.crime_incidents > 0: # Are there more than 1 incident?
                hotspots_values.append(hotspot_incidents.crime_incidents) # Add the crime incident value to list
                roads.remove(hotspot_incidents)  
        if len(hotspots_values) > 0: 
            for i in roads:
                if i.crime_incidents == hotspots_values[0] and len(hotspots) < 5:
                    hotspots.append(i.pos)
                elif i.crime_incidents == hotspots_values[1] and len(hotspots) < 5:
                    hotspots.append(i.pos)
                elif i.crime_incidents == hotspots_values[2] and len(hotspots) < 5:
                    hotspots.append(i.pos)
                elif i.crime_incidents == hotspots_values[3] and len(hotspots) < 5:
                    hotspots.append(i.pos)
                elif i.crime_incidents == hotspots_values[4] and len(hotspots) < 5:
                    hotspots.append(i.pos)
                
            hotspots = [*set(hotspots)] # Remove duplicates

        if len(hotspots) > 0:
            destination_hotspot = self.random.choice(hotspots) # Pick a random hot spot of the five.
        else:
            destination_hotspot = self.random_patrol_node_generator() # If there has been no crime, then give random node.
            
        return destination_hotspot

    def stopsearch(self):
        """
        Stop and search a potential suspect in the same cell as an officer.
        """
        self.stopsearch_score = 0
        # Get information about agents on the same cell.
        same_cell = self.model.grid.get_cell_list_contents(self.pos)
        # Only select agents that are civilians
        filtered_cell = []
        for agent in same_cell:
            if agent.typ == "civilian":
                filtered_cell.append(agent)
        the_police = [self]
        if len(filtered_cell) > 1:
            suspect = self.random.choice([i for i in filtered_cell if i not in the_police])
            if suspect.ethnicity == 'white':
                ethnic_appearance = WHITE_STOP
                prob_stop = WHITE_THRESHOLD
            elif suspect.ethnicity == 'other':
                ethnic_appearance = OTHER_STOP
                prob_stop = OTHER_THRESHOLD
            elif suspect.ethnicity == 'asian':
                ethnic_appearance = ASIAN_STOP
                prob_stop = ASIAN_THRESHOLD
            elif suspect.ethnicity == 'black':
                ethnic_appearance = BLACK_STOP
                prob_stop = BLACK_THRESHOLD
            
            stop_search_probability = suspect.attractiveness + ethnic_appearance

            if  stop_search_probability >= prob_stop:
                suspect.stop_searched += 1


    def step(self):
        """
        A single tick in the simulation. 
        One tick equals to one minute and the agent can move between 6 and 8 steps per tick. 
        """
        if self.moving == "at_the_scene":
            self.time_at_hotspot -= 1

        run_times = self.travel_speed
        if run_times > 0:
            while run_times > 0:
                run_times -= 1
                self.move()
        
        self.stopsearch()