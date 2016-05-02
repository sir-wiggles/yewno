import string
import argparse

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
# Put the passed marker at the beginning of the mine list so when we're 
# descending into the depths, and indexing the new value for the mine,
# we can easily determine if we've hit a mine
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
    With the given Cuboid
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
    def __init__(self, field_file):

        self.mine_locations = []

        fields = map(lambda x: x.strip(), field_file.readlines())
        fields = filter(lambda f: f != '', fields)

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

    def update_depths(self):
        """
        When a ship moves down, it come closer to the mines that remain.
        This will iterate through all known remaining mines and update 
        their depth letter
        """
        for _, _, mine in self.mine_locations:
            mine.update_depth()

    def find_element_bounds(self, ship):
        """
        Finds the smallest possible box that contains all mines plus ship
        """
        ml = self.mine_locations[:]
        ml.append((ship.x, ship.y, ship))

        x_range = sorted(ml, key=lambda c: c[X_INDEX])
        x_max = x_range[-1]
        x_min = x_range[0]


        y_range = sorted(ml, key=lambda c: c[Y_INDEX])
        y_max = y_range[-1]
        y_min = y_range[0]

        return (x_min, x_max), (y_min, y_max)

    def calculate_shift(self, ship):
        """
        Calculates the quadrant with the most space with respect to the ship
        and the dimensions of the new graph
        """
        x = y = 0
        xs = ''
        ys = ''
        for mine in self.mine_locations:
            temp = mine[X_INDEX] - ship.x
            if abs(temp) > x:
                x = abs(temp)
                if temp < 0:
                    xs = '-'
                else:
                    xs = '+'

            temp = mine[Y_INDEX] - ship.y
            if abs(temp)> y:
                y = abs(temp)
                if temp < 0:
                    ys = '-'
                else:
                    ys = '+'
        return xs+ys, (x * 2 + 1, y * 2 + 1)


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
        self.z = MINE_MARKERS[-self.depth-2]
        if self.z == MINE_PASSED_MARKER:
            self.mine_passed = True
            return 
        self.depth += 1

    def link(self, direction, cubby):
        """
        link this Cubby with another Cubby with the given direction.
        Direction should be a string.
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
        Very helpful for debugging, prints out space letter and coordinates
        """
        return '%s (%+d, %+d)' % (self.z, self.x, self.y)


class Ship(object):
    """
    Ship is the object in the Cuboid that can destroy mines. It jumps around
    from Cubby to Cubby occupying that Cubby
    """

    def __init__(self, cuboid, script_file, show_ship=False):

        self.cuboid    = cuboid
        self.show_ship = show_ship
        self.commands  = map(lambda c: c.strip(), script_file.readlines())

        # set the ship at the center of the cuboid zero depth
        self.x = cuboid.dimensions[0]/2 
        self.y = cuboid.dimensions[1]/2 
        self.z = 0
        self.current_cubby = self.cuboid.matrix[self.y][self.x]

        # Variables for scoring
        self.number_of_moves_made    = 0
        self.number_of_vollys_fired  = 0
        self.number_of_initial_mines = len(self.cuboid.mine_locations)
        self.number_of_commands_left = len(self.commands)
        self.starting_score = 10 * self.number_of_initial_mines

        if show_ship:
            self._previous_cubby_marker = self.current_cubby.z
            self.current_cubby.z = SHIP_MARKER

    def radar(self):
        """
        Radar takes the graph and joins the rows into a nice string

        ....c       x, y
        ...#.    a (0, 2)-+
        a....    b (2, 4) |- Points that must be show in graph MARKERS
        .....    # (3, 1) |
        ..b..    c (4, 0)-+

        Find the smallest region bounds that contain all elements
            x bounds
                max(MARKERS) on x = 3
                min(MARKERS) on x = 0

            y bounds
                max(MARKERS) on y = 4
                min(MARKERS) on y = 1

        Find the vector between ship and mines 
            a - # = (0, 2) - (3, 1) = (-3, 1)
            b - # = (2, 4) - (3, 1) = (-1, 3) Ship to mine vectors SMV
            c - # = (4, 0) - (3, 1) = (1, -1)

        Find the display bounds
            x: max(abs(SMV)) * 2 + 1 = 3 * 2 + 1 = 7
            y: max(abs(SMV)) * 2 + 1 = 3 * 2 + 1 = 7
                 
            --           +-
                .....|..
                .....|..
                -----+--
                @...c|..    
                ...#.|..    
                a....|..    
                .....|..
                ..b..|..
            -+           ++

            x: sign of the max abs(SMV.x)
            y: sign of the max abs(SMV.y) -> element in ['--', '+-', '-+', '++', '-', '+']

            This symbol will indicate how to shift the sub matrix in the blank matrix

        This just feels so wrong.
        """
        
        xb, yb = self.cuboid.find_element_bounds(self.current_cubby)
        shift, dimension = self.cuboid.calculate_shift(self.current_cubby)

        # this blank matrix will encompass the Cuboid matrix
        blank = []
        for y in xrange(abs(dimension[Y_INDEX])):
            row = []
            for x in xrange(abs(dimension[X_INDEX])):
                row.append('.')
            blank.append(row)

        # slice up the matrix to account for the cuboid shrinking. 
        # We do this so it can properly fix inside the blank matrix
        sub = self.cuboid.matrix[yb[0][Y_INDEX]:yb[1][Y_INDEX]+1]
        for i, row in enumerate(sub):
            sub[i] = row[xb[0][X_INDEX]: xb[1][X_INDEX]+1]

        # decide how the sub matrix should be shifted within the blank matrix
        if shift in ["++", "+"]:
            y_start = len(blank) - len(sub)
            x_start = len(blank[0]) - len(sub[0])
        elif shift in ["--", "-", ""]:
            y_start = 0
            x_start = 0
        elif shift == "+-":
            y_start = 0
            x_start = len(blank[0]) - len(sub[0])
        elif shift == "-+":
            y_start = len(blank) - len(sub)
            x_start = 0
        else:
            print ":P", shift

        # take the elements from the sub matrix and place them at 
        # appropriate coordinate
        for y, row in enumerate(sub, start=y_start):
            for x, cubby in enumerate(row, start=x_start):
                blank[y][x] = cubby.z

        # put all the lines together for printing
        lines = []
        for row in blank:
            lines.append(''.join(row))
        return '\n'.join(lines)

    def execute_command_scrip_file(self):
        """
        run takes the script and executes the commands in that script
        """
        for step_count, command in enumerate(self.commands, start=1):
            self.number_of_commands_left -= 1

            print "Step %d\n\n%s\n\n%s\n" % (step_count, self.radar(), command)

            self._execute_command(command)

            # Checks if the current state is pass fail or still running
            pass_fail, score = self.check_score()
            if pass_fail is not None:
                print "%s\n\n%s %s" % (self.radar(), pass_fail, score)
                break
            print "%s\n" % self.radar()

    def _execute_command(self, command):
        torpedoe, movement = self._handle_command_line(command)

        if torpedoe:
            self._handle_torpedoe(torpedoe)

        if movement:
            self._handle_movement(movement)

        # update depths before checking scores to see if we have passed any mines
        # in this turn
        self.cuboid.update_depths()

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
        # Empty strings would occur if you have a command and a movement separated 
        # by more than one space.
        commands = filter(lambda c: c != "", command_line.split(' '))

        movement = torpedoe = None
        if len(commands) == 2:
            torpedoe, movement = commands
            torpedoe = torpedoe if torpedoe in FIRING_PATTERN_MAP else None
            movement = movement if movement in MOVEMENT_MAP else None
        elif len(commands) == 1:
            # one arg could mean a movement or a torpedo so we need to figure that out.
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
        # eight points on a compass
        pattern = FIRING_PATTERN_MAP[torpedoe]
    
        # handle each pattern
        for p in pattern:
            # Pulling the pattern out of the MOVEMENT_MAP will give us the
            # compass directions i.e. north, south, ...
            directions = MOVEMENT_MAP[p]

            # Don't change the ships current Cubby, so we'll copy it and 
            # do operations on the copy
            temp_cubby = self.current_cubby 

            # Handle the compass moves from the directions. This is a list of
            # compass directions at most two and at least one
            for move in directions:
                # because the outer ring of the matrix doesn't have neighbors for 
                # some directions, it's possible to have temp_cubby as None in which 
                # case AttributeErros will occur if we don't check for them
                if temp_cubby is None:
                    break

                # If the direction was down, we're not changing to a different
                # Cubby but handling the one we're on. This is a special case
                if move == DOWN:
                    break

                # get the attribute from the temp Cubby that is the move compass string
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

        if self.show_ship:
            self.current_cubby.z = self._previous_cubby_marker

        # Move the ship to the Cubby indicated by the movement
        self.current_cubby = getattr(self.current_cubby, movement)

        if self.show_ship:
            self._previous_cubby_marker = self.current_cubby.z
            self.current_cubby.z = SHIP_MARKER

    def __repr__(self):
        """
        Again helpful for debugging
        """
        return '(%+d, %+d, %+d)' % (self.x, self.y, self.z)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument('field_file', help='path to field file')
    parser.add_argument('script_file', help='path to script file')
    parser.add_argument('--show-ship', action='store_true', help="shows the # symbol for where the ship is in the graph")

    args = parser.parse_args()

    ff = open(args.field_file, 'rb')
    sf = open(args.script_file, 'rb')

    cuboid = Cuboid(ff)
    ship = Ship(cuboid, sf, show_ship=args.show_ship)
    ship.execute_command_scrip_file()

