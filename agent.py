from random import randint
from turtle import right
from mesa import Agent
from numpy import random
import operator

#----------------------
class StreetPatch(Agent):
    """An agent that will be a patch in the map"""

    def __init__(self, unique_id, model, position):
        '''sets up the agent instance'''
        super().__init__(unique_id, model)

        #Create a list of x and y cor to generate a grid layout.
        roads_xcor = list(range(0,100,3))
        roads_ycor = list(range(0,120,6))
        self.pos = position

        if(self.pos[0] in roads_xcor) or (self.pos[1] in roads_ycor):
            self.typ = 'road'
        else:
            self.typ = 'streetpatch'       

#----------------------
class Civilian(Agent):
    """
    A member of the general population, which can be a victim of street robbery.
    """
    def __init__(self, unique_id, model, position, prev_position, activity_nodes, moving, destination, timer):
        super().__init__(unique_id, model)
        self.pos = position
        self.typ = 'civilian'
        self.ethnicity = self.assign_ethnic()       
        #Agent movement:
        self.home = position
        self.prev_pos = prev_position
        self.activity_nodes = activity_nodes
        self.moving = moving
        self.destination = destination
        self.timer = timer
        print("Nodes:", activity_nodes)

    def move(self):
        '''
        Inspect neighbours and move to the next cell towards the destination patch. 
        '''
        if self.moving == "moving":
            if self.pos == self.home:
                self.destination = self.random.choice(self.activity_nodes)
            elif self.pos == self.destination:
                if randint(0,100) <= 79:
                    self.destination = self.home
                else:
                    self.destination = self.random.choice([a_node for a_node in self.activity_nodes if a_node not in self.pos])
            # Create list of possible neighbouring cells to move to. 
            self.update_neighbors()
            road_neighbours = []
            for agent in self.neighbors:
                if agent.pos == self.destination:
                    self.model.grid.move_agent(self, self.destination) # Do nothing. 
                else:
                    if agent.typ == 'road': 
                        road_neighbours.append(agent.pos) #Fix this!!!!!!!

            # Check if agent has arrived. If agent has arrived at destination: set moving to "arrived". 
            if self.destination == self.pos and self.moving == "moving":  
                #self.model.grid.move_agent(self, self.pos)
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
                random_integer = randint(0, 100)
                if ((random_integer <= 98) and (len(right_dir) > 0)):
                    if (len(right_dir) > 1):
                        for c in right_dir:
                            if ((abs(distance[0]) >= abs(distance[1])) and (c[0] != self.pos[0])):
                                best_position = c
                            elif ((abs(distance[0]) <= abs(distance[1])) and (c[1] != self.pos[1])):
                                best_position = c
                        ri = randint(0,100)
                        if ((ri > 80) and best_position):
                                new_position = best_position
                        else:
                                new_position = self.random.choice(right_dir) # move in right direction
                    else:
                        new_position = self.random.choice(right_dir) # move in the right direction
                else:
                    if (len(wrong_dir) > 0):
                        new_position = wrong_dir[0] # move in the wrong dir
                    else:
                        new_position = self.pos # stand still
                
                self.prev_pos = self.pos
                self.model.grid.move_agent(self, new_position)
        
        elif self.moving == "arrived":
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

    def update_neighbors(self):
        '''
        Look around and identify the neighbours.
        '''
        self.neighborhood = self.model.grid.get_neighborhood(
            self.pos, moore=False, radius=1
        )
        self.neighbors = self.model.grid.get_cell_list_contents(self.neighborhood)

    def step(self):
        '''
        A single tick in the simulation.
        '''
        self.move()

    def assign_ethnic(self):
        '''
        Assign ethnic background to the population. Data is based on London population 2020.
        Change to set number.
        '''
        rand_nr = randint(0,101)
        white_pop = 44.9
        other_pop = 23.3
        asian_pop = 18.5
        black_pop = 13.3

        if rand_nr <= white_pop:
            ethnicity = "white"
        elif white_pop < rand_nr <= (other_pop + white_pop):
            ethnicity = "other"
        elif (white_pop + other_pop) < rand_nr <= (other_pop + white_pop + asian_pop):
            ethnicity = "asian"
        else:
            ethnicity = "black"
        
        return ethnicity

#----------------------