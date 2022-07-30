from random import randint
from mesa import Agent
import operator
import random


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
    def __init__(self, unique_id, model, position, prev_position):
        super().__init__(unique_id, model)
        # Every agent has a race
        self.pos = position
        self.typ = 'civilian'
        self.ethnicity = self.assign_ethnic()
        self.prev_pos = prev_position
    
    def move(self):
        """
        Inspect neighbours and move to the next road patch. 
        """
        self.update_neighbors()
        road_neighbours = []
        for agent in self.neighbors:
            if agent.typ == 'road': 
                road_neighbours.append(agent.pos)
        
        test_coord = (9,20)
        right_dir = []
        wrong_dir = []
        

        if test_coord == self.pos:
            new_position = self.pos    
            self.model.grid.move_agent(self, self.pos)
        else:
            distance = tuple(map(operator.sub, test_coord, self.pos))
            for coordinate in road_neighbours:
                if coordinate != self.prev_pos:
                    next_distance = tuple(map(operator.sub, test_coord, coordinate))
                    if ((abs(next_distance[0]) < abs(distance[0])) or (abs(next_distance[1]) < abs(distance[1]))):
                        right_dir.append(coordinate)
                    else:
                        wrong_dir.append(coordinate)
            print("right_dir:", right_dir)
            print("wrong_dir:", wrong_dir)
            random_integer = randint(0, 101)
            if ((random_integer <= 98) and (len(right_dir) > 0)):
                new_position = random.choice(right_dir) # move in right direction
            #elif (90 < random_integer <= 95 and (len(wrong_dir) > 0)):
                #new_position = random.choice(wrong_dir) # move in wrong direction
            #elif (95 < random_integer < 99):
                #new_position = self.pos # stand still
            else:
                #new_position = self.prev_pos # go back to previous pos
                if (len(wrong_dir) > 0):
                    new_position = wrong_dir[0]
                else:
                    new_position = self.pos
            self.prev_pos = self.pos
            self.model.grid.move_agent(self, new_position)
            print("I am", self.ethnicity)

    def update_neighbors(self):
        """
        Look around and identify the neighbours.
        """
        self.neighborhood = self.model.grid.get_neighborhood(
            self.pos, moore=False, radius=1
        )
        self.neighbors = self.model.grid.get_cell_list_contents(self.neighborhood)

    def step(self):
        self.move()
    
    def assign_ethnic(self):
        """
        Assign ethnic background to the population. Data is based on London population 2020.
        """
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