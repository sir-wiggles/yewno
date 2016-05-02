import string

# These are the valid commands that can be entered into a script file
# Direction name mappings 
NORTH = 'north'
SOUTH = 'south'
EAST  = 'east'
WEST  = 'west'
DOWN  = ''

# Torpedo name mappings
ALPHA = 'alpha'
BETA  = 'beta'
GAMMA = 'gamma'
DELTA = 'delta'

# let's just keep the pattern going
PASS = 'pass'
FAIL = 'fail'

# How objects in the cuboid are represented. For debugging purposes, I
# gave the ship a marker symbol to see where the ship was in the graph
SHIP_MARKER = '#'
MINE_PASSED_MARKER = '*'
EMPTY_SPACE_MARKER = '.'
# Put the passed marker at the benning of the mine list so when we're 
# decending into the depths, and indexing the new value for the mine,
# we can easly determine if we've hit a mine
MINE_MARKERS = MINE_PASSED_MARKER + string.ascii_letters

# Positions of x, y, z values in tuples passed around in various places
X_INDEX = 0
Y_INDEX = 1
Z_INDEX = 2

# To be used in making the map dynamic 
DIRECTION_COMPLEMENT_MAP = {
    NORTH: SOUTH,
    SOUTH: NORTH,
    EAST: WEST,
    WEST: EAST
}

# How to translate to and from coordinates and word movements
MOVEMENT_MAP = {
    NORTH   : ( 0,  1),
    SOUTH   : ( 0, -1),
    EAST    : ( 1,  0),
    WEST    : (-1,  0),
    (-1, -1): [SOUTH, WEST],
    (-1,  0): [WEST],
    (-1,  1): [NORTH, WEST],
    ( 0,  1): [NORTH],
    ( 1,  1): [NORTH, EAST],
    ( 1,  0): [EAST],
    ( 1, -1): [SOUTH, EAST],
    ( 0, -1): [SOUTH],
    ( 0,  0): [DOWN]
}

# The firing pattern of the torpedoes
FIRING_PATTERN_MAP = {
    ALPHA: [(-1, -1), (-1,  1), ( 1, -1), ( 1,  1)],
    BETA : [(-1,  0), ( 0, -1), ( 0,  1), ( 1,  0)],
    GAMMA: [(-1,  0), ( 0,  0), ( 1,  0)],
    DELTA: [( 0, -1), ( 0,  0), ( 0,  1)]
}

class Cuboid(object):
    """
    Cuboid is the space representing the mine field. It is a matrix
    where every element in the matrix is a Cubby linked with all their 
    neighbors.

    For example:
    With the givin Cuboid
        cuboid = [
            [0, 1, 2],      North
            [3, 4, 5],  West  +  East
            [6, 7, 8]       South
        ]
    where each element is a Cubby represented by a number here.

    When the Cuboid is constructed, each Cubby is linked with its immediate
    neighbors to the north, south, east, west.

    Cubby 0 has neighbors 
        0.north = None    because there are no elements above it 
        0.east = 1        east is to the right and that is 1 in this case
        0.south = 3       south is below which is 3 in this case
        0.west = None     because there are no elements to the left of it

    In this example Cubby 4 is all neighbors accounted for

    Neighbors are simple attributes on the Cubby itself.
    """
    def __init__(self, field):

        self.mine_locations = []
        fields = map(lambda x: x.strip(), field.split('\n'))

        matrix = []
        cubby_id = 0
        for y, line in enumerate(fields):
            row = []
            previous_cubby = None
            for x, depth in enumerate(line):
                cubby = Cubby(x, y, depth, cubby_id)
                cubby_id += 1
                row.append(cubby)
                if depth != EMPTY_SPACE_MARKER:
                    self.mine_locations.append(cubby.mine_location())
                if previous_cubby:
                    cubby.link(WEST, previous_cubby)
                    previous_cubby.link(EAST, cubby)
                previous_cubby = cubby
            if len(matrix) > 0:
                for x, cubby in enumerate(row):
                    previous_cubby = matrix[-1][x]
                    cubby.link(NORTH, previous_cubby)
                    previous_cubby.link(SOUTH, cubby)
            matrix.append(row)

        self.matrix = matrix
        self.dimensions = (len(matrix), len(matrix[0]), 0)

    def remove_mine_location(self, mine):
        """
        Given a mine, remove the mine at that location and pop them 
        out of the known mine locations.
        """
        mine_index = 0
        for i, m in enumerate(self.mine_locations):
            if m[2].id == mine.id:
                mine_index = i
                break
        self.mine_locations.pop(mine_index)

    def graph(self):
        """
        Return a graph of the cuboid.
        """
        display = [] 
        for row in self.matrix:
            line = []
            for col in row:
                line.append(col.z)
            display.append(line)
        return display

    def update_depths(self, depth):
        """
        When a ship moves down, it come closer to the mines that remain.
        This will iterate throught all known remaining mines and update 
        their depth letter
        """
        for _, _, mine in self.mine_locations:
            mine.update_depth()


class Cubby(object):
    """
    Cubby is a 1x1 element in the Cuboid that is either an empty space,
    a mine or the ship
    """

    def __init__(self, x, y, z, cubby_id):
        self.x = x
        self.y = y
        self.z = z
        self.id = cubby_id

        if z != EMPTY_SPACE_MARKER:
            self.depth = -1 * (MINE_MARKERS.find(z) + 1)
            self.mine  = True
        else:
            self.depth = None
            self.mine  = False

        self.mine_passed = False

        # neighbors
        self.north = None
        self.south = None
        self.east  = None
        self.west  = None

    def destroy_mine(self):
        """
        Will remove the mine if it is a mine and the ship hasn't already
        passed the mine depth.
        """
        if self.mine == True and self.z != MINE_PASSED_MARKER:
            self.mine = False
            self.z = EMPTY_SPACE_MARKER
            self.depth = None
            return True
        return False

    def update_depth(self):
        """
        Will decrease the depth and set the new space letter.
        """
        self.z = string.ascii_letters[-self.depth-3]
        if self.z == MINE_PASSED_MARKER:
            self.mine_passed = True
            return 
        self.depth += 1

    def link(self, direction, cubby):
        """
        link this cubby with another cubby with the given direction.
        direction should be a string.
        """
        setattr(self, direction, cubby)
        return self

    def mine_location(self):
        """
        return the x and y of this mine as well as itself not sure why I'm returning
        self now that I look at this.
        """
        return (self.x, self.y, self)

    def __repr__(self):
        """
        Very helpful for debuggin, prints out spaec letter and coordinates
        """
        return '%s (%+d, %+d)' % (self.z, self.x, self.y)


class Ship(object):
    """
    Ship is the object in the Cuboid that can destroy mines. It jumps around
    from cubby to cubby occupying that cubby
    """

    def __init__(self, cuboid):

        self.cuboid = cuboid

        # set the ship at the center of the cuboid zero depth
        self.x = cuboid.dimensions[0]/2 
        self.y = cuboid.dimensions[1]/2 
        self.z = 0
        self.current_cubby = self.cuboid.matrix[self.y][self.x]

        # Variables for scoring
        self.number_of_vollys_fired = 0
        self.number_of_moves_made = 0
        self.number_of_initial_mines = len(self.cuboid.mine_locations)
        self.starting_score = 10 * self.number_of_initial_mines

        # TODO: remove before sending
        self._previous_cubby_marker = self.current_cubby.z
        self.current_cubby.z = SHIP_MARKER
        # TODO: remove before sending

    def radar(self):
        """
        Radar takes the graph and joins the rows into a nice string
        """
        lines = []
        for row in self.cuboid.graph():
            lines.append(''.join(row))
        return '\n'.join(lines)

    def run(self, script):
        """
        run takes the script and executes the commands in that script
        """
        commands = map(lambda x: x.strip(), script.split('\n'))
        self.number_of_commands_left = len(commands)
        for step_count, command in enumerate(commands, start=1):
            self.number_of_commands_left -= 1

            print "Step %d\n" % step_count
            print "%s\n" % self.radar()
            print "%s\n" % command

            torpedoe, movement = self._handle_command_line(command)

            if torpedoe:
                self._handle_torpedoe(torpedoe)

            if movement:
                self._handle_movement(movement)

            pass_fail, score = self.check_score()
            if pass_fail is not None:
                print "%s\n" % self.radar()
                print '%s %s' % (pass_fail, score)
                return 
            self.cuboid.update_depths(self.z)
            step_count += 1

            print "%s\n" % self.radar()

    def check_score(self):
        """
        Check to see if the various pass fail cases are met and return the state and score
        otherwise return an empty string indicating we are still running.
        """
        # Case 1. Passed a mine
        for mine in self.cuboid.mine_locations:
            if mine[2].mine_passed == True:
                return FAIL, 0
        
        # Case 2. Script completed but mines still remain
        if self.number_of_commands_left == 0 and len(self.cuboid.mine_locations) != 0:
            return FAIL, 0

        # Case 3. All mines cleared with steps remaining
        if self.number_of_commands_left != 0 and len(self.cuboid.mine_locations) == 0:
            return PASS, 1

        # Case 4. All mines cleared and no steps remaining
        if self.number_of_commands_left == 0 and len(self.cuboid.mine_locations) == 0:

            volly_score = self.number_of_vollys_fired * 5
            volly_max = self.number_of_initial_mines * 5
            if volly_score > volly_max:
                final_volly_score = volly_max
            else:
                final_volly_score = volly_score

            move_score = self.number_of_moves_made * 2 
            move_max = self.number_of_initial_mines * 3
            if move_score > move_max:
                final_move_score = move_max
            else:
                final_move_score = move_score

            return PASS, self.starting_score - final_volly_score - final_move_score

        return None, -1

    def _handle_command_line(self, command_line):
        # split the line on space and filter out anything that is an empty string.
        # Empty strings would occure if you have a command and a movement seperated
        # by more than one space.
        commands = filter(lambda c: c != "", command_line.split(' '))

        movement = torpedoe = None
        if len(commands) == 2:
            torpedoe, movement = commands
            torpedoe = torpedoe if torpedoe in FIRING_PATTERN_MAP else None
            movement = movement if movement in MOVEMENT_MAP else None
        elif len(commands) == 1:
            # one arg could mean a movement or a torpedoe so we need to figure that out.
            command = commands[0]
            if command in MOVEMENT_MAP:
                movement = command
            else:
                torpedoe = command

        if movement != "":
            self.z -= 1

        return (torpedoe, movement)

    def _handle_torpedoe(self, torpedoe):
        """
        handles a firing pattern from the user script
        """
        self.number_of_vollys_fired += 1

        # Get the firing pattern out of the mapping.  This will be a
        # list of tuples where each tuple is a vector representing 
        # eight points on a compus
        pattern = FIRING_PATTERN_MAP[torpedoe]
    
        # handle each pattern
        for p in pattern:
            # Pulling the pattern out of the MOVEMENT_MAP will give us the
            # compus directions i.e. north, south, ...
            directions = MOVEMENT_MAP[p]

            # Don't change the ships current Cubby, so we'll copy it and 
            # do operations on the copy
            temp_cubby = self.current_cubby 

            # Handle the compus moves from the directions. This is a list of
            # compus directions at most two and at least one
            for move in directions:
                # because the outer ring of the matrix doesn't have neighbors for 
                # some directions, it's possible to have temp_cubby as None in which 
                # case AttributeErros will occure if we don't check for them
                if temp_cubby is None:
                    break

                # If the direction was down, we're not changing to a different
                # Cubby but handeling the one we're on. This is a special case
                if move == DOWN:
                    break

                # get the attribute from the temp Cubby that is the move compus string
                # For example let's say directions is ["north", "west"] then move
                # will first be "north" getting the "north" neighbor and saving that
                # as the temp_cubby and doing the process again for the second command
                # "west"
                # this is equivalent to temp_cubby.north.west
                temp_cubby = getattr(temp_cubby, move)

            # If we have a Cubby when issue the destroy_mine 
            if temp_cubby and temp_cubby.destroy_mine():
                self.cuboid.remove_mine_location(temp_cubby)

    def _handle_movement(self, movement):
        # z axis movements don't get counted as movements for scoring
        if movement != DOWN:
            self.number_of_moves_made += 1

        # Get the coordinates out the of MOVEMENT_MAP in the form (x:int, y:int)
        x, y = MOVEMENT_MAP[movement]
        self.x += x
        self.y += y

        # TODO: remove befor sending
        self.current_cubby.z = self._previous_cubby_marker
        # TODO: remove befor sending

        # Move the ship to the cubby indicated by the movement
        self.current_cubby = getattr(self.current_cubby, movement)

        # TODO: remove before sending
        self._previous_cubby_marker = self.current_cubby.z
        self.current_cubby.z = SHIP_MARKER
        # TODO: remove before sending


    def __repr__(self):
        """
        Again helpful for debuggin
        """
        return '(%+d, %+d, %+d)' % (self.x, self.y, self.z)


if __name__ == "__main__":

    field = '''..Z..
               .....
               Z...Z
               .....
               ..Z..'''

    script = '''north
                delta south
                west
                gamma east
                east 
                gamma west
                south
                delta '''

    cuboid = Cuboid(field)
    ship = Ship(cuboid)
    ship.run(script)

