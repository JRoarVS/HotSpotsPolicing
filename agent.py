from random import randint
from mesa import Agent
from numpy import random
import operator
from operator import attrgetter


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
    ethnicity):
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
                self.timer = 1 + int(random.uniform(0, 6)) # Home Node = 1 tick + U(0, 600)
            else:
                self.timer = 15 + int(random.uniform(0,4)) # Activity Node = 15 ticks + U(0, 480)
        else:   
            if self.timer == 0:
                self.moving = "moving"
            else: 
                self.timer -= 1

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
                if self.cop_nearby():
                    print("There was cops nearby")
                else:
                    road_risk = 10 # Road risk can't be 10 
                    for f in same_cell:
                        if f.typ == "road":
                            road_risk = f.risk
                    if road_risk < 10:
                        Nc = (len(filtered_cell) - 2) + victim.perceived_guardianship
                        guardianship = self.perceived_capability + Nc 
                        rational_choice_score = victim.attractiveness - guardianship + self.criminal_propensity + road_risk
                        print("Tot score:", rational_choice_score, "Attractiveness:", victim.attractiveness, "Guardianship:", guardianship, "Motivation:", self.criminal_propensity, "Risk:", road_risk)
                        if rational_choice_score >= 10: # CHANGE TO 20!!!!!
                            self.robbery()
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
    
    def robbery(self):
        return
    
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

    def move(self):
        """
        Inspect neighbours and move to the next cell towards the destination patch. 
        """
        if self.moving == "moving":
            if self.pos == self.destination:
                if self.hotspot_patrol:
                    self.destination = self.hotspot_node_generator()
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
        roads = [obj for obj in self.model.schedule.agents if isinstance(obj, StreetPatch)]
        hotspot = max(roads, key=attrgetter("crime_incidents")).pos
        if len(hotspot) > 0:
            xy = hotspot
        else:
            xy = self.random_patrol_node_generator() # If there has been no crime, then give random node.

        return (xy)

    def stopsearch(self):
        """
        Check if a suitable suspect is in the same cell.
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
                if self.cop_nearby():
                    print("There was cops nearby")
                else:
                    road_risk = 10 # Road risk can't be 10 
                    for f in same_cell:
                        if f.typ == "road":
                            road_risk = f.risk
                    if road_risk < 10:
                        Nc = (len(filtered_cell) - 2) + victim.perceived_guardianship
                        guardianship = self.perceived_capability + Nc 
                        rational_choice_score = victim.attractiveness - guardianship + self.criminal_propensity + road_risk
                        print("Tot score:", rational_choice_score, "Attractiveness:", victim.attractiveness, "Guardianship:", guardianship, "Motivation:", self.criminal_propensity, "Risk:", road_risk)
                        if rational_choice_score >= 10: # CHANGE TO 20!!!!!
                            self.robbery()
                            victim.N_victimised += 1
                            if self.criminal_propensity < 10:
                                self.time_to_offending = self.time_to_offending_again()
                                neighbours = self.model.grid.get_neighborhood(
                                self.pos, moore=False, include_center = True, radius=2)                                 
                                whos_here = self.model.grid.get_cell_list_contents(neighbours)
                                for road in whos_here:
                                    if road.typ == "road":
                                        road.crime_incidents += 1
                    return
                return

    def step(self):
        """
        A single tick in the simulation. 
        One tick equals to one minute and the agent can move between 6 and 8 steps per tick. 
        """
        run_times = self.travel_speed
        if run_times > 0:
            while run_times > 0:
                run_times -= 1
                self.move()