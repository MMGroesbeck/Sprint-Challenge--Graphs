import copy
from collections import deque

# Scout object to explore/traverse map:
# Takes room object, not room id
class Scout:
    def __init__(self, room, world, lefty=True, compass=None):
        self.room = room
        self.world = world
        # lefty and compasses represent directional preferences when choice is arbitrary
        # different mazes will have different optimal permutation
        self.lefty = lefty
        if compass is None:
            self.compass = ["n", "e", "s", "w"]
        else:
            self.compass = compass
        if lefty:
            ind = [0, 1, 2, 3]
        else:
            ind = [0, -1, -2, -3]
        self.compasses = [[self.compass[(i + j) % 4] for i in ind] for j in ind]
        self.decision_counter = 0
        # facing = index of self.compass for current direction
        self.facing = 0
        # visited: set of room IDs
        self.visited = set([room.id])
        # steps: directions moved (e.g. "n", "e")
        self.steps = []
    # turn_left and turn_right are not strictly left/right turns unless self.compass is a rotation of ["n", "e", "s", "w"]
    def turn_left(self):
        self.facing = (self.facing - 1) % 4
    def turn_right(self):
        self.facing = (self.facing + 1) % 4
    def check_new_adjacent(self, room=None):
        # Returns True if any adjacent rooms have not been visited
        if room == None:
            room = self.room
        for exit in self.room.get_exits():
            if room.get_room_in_direction(exit).id not in self.visited:
                return True
        return False
    def move_direction(self, direction):
        # Moves without changing facing direction
        if direction in self.room.get_exits():
            self.steps.append(direction)
            self.room = self.room.get_room_in_direction(direction)
            self.visited.add(self.room.id)
    # For mode 1: explore contiguous sets of unvisited rooms
    # When more than one choice available, search shortest branch first
    def branch_eval(self, room):
        # Returns number of contiguous unvisited rooms starting from room parameter
        checked = set([room.id])
        branch_deque = deque([room.id])
        while len(branch_deque) > 0:
            this_room_id = branch_deque.popleft()
            this_room = self.world.rooms[this_room_id]
            if this_room_id not in checked and this_room_id not in self.visited:
                checked.add(this_room_id)
            for exit in this_room.get_exits():
                new_room_id = this_room.get_room_in_direction(exit).id
                if new_room_id not in checked and new_room_id not in self.visited:
                    branch_deque.append(new_room_id)
        return len(checked)
    def automap(self):
        # Continue while an adjacent unvisited room is available:
        while self.check_new_adjacent():
            # Scout chirality represents preferred direction
            # (relative to direction of room entrance)
            if self.lefty:
                self.turn_left()
            else:
                self.turn_right()
            # At intersections, choosing shortest branch reduces backtracking:
            # Evaluate how many contiguous unvisited squares are accessible in each direction:
            branches = {i: None for i in self.compass}
            for d in self.room.get_exits():
                if self.room.get_room_in_direction(d).id not in self.visited:
                    branches[d] = self.branch_eval(self.room.get_room_in_direction(d))
            shortest = self.compass[self.facing]
            # Choice among available moves with equal branch size is in clockwise compass order:
            for turn in self.compasses[self.facing]:
                if branches[shortest] is not None and branches[turn] is not None:
                    if branches[turn] < branches[shortest]:
                        shortest = turn
                    if branches[turn] == branches[shortest] and turn != shortest:
                        self.decision_counter += 1
                elif branches[shortest] == None:
                    shortest = turn
            # Move in direction of shortest branch
            self.facing = self.compass.index(shortest)
            self.move_direction(shortest)
    # For mode 2: find and follow shortest path to visited room with unvisited neighbor
    def nearest_new(self):
        # Returns path to nearest room with unvisited neighbor
        checked = set()
        room_deque = deque([[self.room.id, []]])
        while (len(room_deque) > 0):
            this_state = room_deque.popleft()
            if this_state[0] not in self.visited:
                # this_state includes unvisited room, so do not return last step
                return this_state[1][:-1]
            else:
                room = self.world.rooms[this_state[0]]
                checked.add(room)
                for exit in room.get_exits():
                    if room.get_room_in_direction(exit) not in checked:
                        new_state = copy.deepcopy(this_state)
                        new_state[0] = room.get_room_in_direction(exit).id
                        new_state[1].append(exit)
                        room_deque.append(new_state)
        return []
    def go_to_new(self):
        # Gets list of directions to nearest room with unvisited neighbor:
        for step in self.nearest_new():
            # Follow those directions (not changing facing direction)
            self.move_direction(step)
        # Update facing to reflect most recent move
        facing = self.compass.index(self.steps[-1])