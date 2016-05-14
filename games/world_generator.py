#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import math
import random
import sys
import pokeygame
import argparse
import inspect
import logging
import time
from pathfinder import Pathfinder, GraphGrid
from pokeyworks import ColorIze as color
from tiles import  WorldTile
from pokeyworks import setup_logger as logger

class WorldGenerator:

    """ Generates worlds based on the config parameters """

    def __init__(
                self,           # World Generator
                debug=False,    # Debug mode
                silent=False,   # Silent mode
                rand=False,     # Random mode
                fpath=None,     # Output file path
                conf=None,      # Config file path
                dim_x=25,       # x dimension range
                dim_y=25,       # y dimension range
                dim_z=3,        # z dimension range
                flex_limit=0,   # Maximum dimension fluctuation
                verbose=False,  # Verbose mode
                app_logger=None,# Optional passed logger
                room_variance=2,# Room size variance
                post_check=False,# Automatic post-generation check
                path_alg='gbf_search'   # Path testing algorithm
                ):
        """ WorldGenerator creates a world_template """

        # The WorldGenerator.grid template can be read directly
        # by importing as a module, or loaded from the output
        # of the command-line invoked menu.  Output format:
        #
        #   map_template = (((t...),...(t'...))...
        #
        # Where T are tile type codes for your interpreter
        # or WorldTile tile types if using pokeygame
        #
        # Template features :
        #
        #   Randomized templates of any integer dimension can be generated.
        # A series of waypoints are generated randomly across each level,
        # which are then connected by hallway.  Rooms are generated at the
        # waypoints of varying sizes (control by setting room_variance),
        # and a pathfinding algorithm ensures each level is passable before
        # being returned.

        start = time.clock()
        self.history = []
        self.silent = silent

        if app_logger is None:
            # Enable verbose messages if in debug or verbose mode
            if debug or verbose:
                log_level = logging.DEBUG
            elif silent:
                log_level = logging.ERROR
            else:
                log_level = logging.INFO
            # Engage the logger
            self.logger = logger(__name__,log_level)
            self.logger.info('[*] WorldGenerator logger engaged')
        else:
            self.logger = app_logger
            self.logger.info('[*] Logger received')


        # Designate bottom floor as boss level
        self.boss_level = dim_z     # Boss on lowest level
        self.logger.debug('\tBoss on {}'.format(self.boss_level))

        self.logger.debug("\tdim_x={}".format(dim_x))
        self.logger.debug("\tdim_y={}".format(dim_y))
        self.logger.debug("\tdim_z={}".format(dim_z))
        self.dim_x = int(dim_x)
        self.dim_y = int(dim_y)
        self.dim_z = int(dim_z)
        self.post_done = False  # Flag to indicate post-generation path check
        self.min_dist = int(((self.dim_x+self.dim_y)/2)*.75)   #3/4 the avg
        self.logger.debug(
                '\tMinimum waypoint distance : {}'.format(self.min_dist)
                )

        self.grid = self.erect_walls()    # fill the dict with walls
        self.dims = (dim_x,dim_y,dim_z)
        self.logger.debug(
                '\tDimensions (x,y,z): ( {}, {}, {} )'.format(*self.dims)
                )

        # Map Generation Functions
        self.logger.info('[*] Generating map template')

        self.logger.info('[*] Generating waypoints')
        self.set_entry_point()
        self.set_descent_point()
        self.set_exit_point()

        self.logger.info('[*] Filling map content')
        self.build_paths()
        self.build_rooms()

        if post_check:
            self.logger.info('[*] Testing map pathing')
            self.test_paths()

        self.logger.info('[*] Map generation complete')
        self.logger.debug('\tTook {}s'.format(time.clock()-start))

    def __str__(self):
        retval = ''
        for z in range(0,self.dim_z+1):
            retval+='\tFloor -{0}-\n'.format(z)
            for y in range(0,self.dim_y):
                for x in range(0,self.dim_x):
                    if self.grid[x,y,z][0]==WorldTile.wall:
                        retval += '. '
                    else:
                        retval += '.'
                        if self.grid[x,y,z][1] is not None:
                            retval+=color(
                                    '{0}'.format(self.grid[x,y,z][0]),
                                    self.grid[x,y,z][1]
                                    ).colorized
                        else:
                            retval+= '{0}'.format(self.grid[x,y,z][0])
                retval+='\n'

        return retval

    def erect_walls(self):
        grid = {}

        start = time.clock()
        self.logger.info('[*] Building walls')

        for z in range(0,self.dim_z+1):
            for y in range(0,self.dim_y):
                for x in range(0,self.dim_x):
                    # Grid format [tile_value,color(None if normal color)]
                    grid[x,y,z]=[WorldTile.wall,None]

        self.logger.debug('\tFilled {} tiles'.format(len(grid)))
        self.logger.debug('\tTook {}s'.format(time.clock()-start))

        return grid

    def set_entry_point(self):
        """ Sets the initial entry point on the map edge """

        start = time.clock()
        self.logger.info('[*] Setting entry point')

        z = 0   # Entry point is on first floor
        valid_x = range(1,self.dim_x-1) # valid values (OR w/valid_y)
        valid_y = range(1,self.dim_y-1)

        self.logger.debug('\tvalid_x range : {}'.format(valid_x))
        self.logger.debug('\tvalid_y range : {}'.format(valid_y))

        iterations = 0
        while True:
            x_test = random.randint(0,self.dim_x)
            y_test = random.randint(0,self.dim_y)

            if x_test in valid_x and y_test not in valid_y:
                condition = True
            elif y_test in valid_y and x_test not in valid_x:
                condition = True
            else:
                condition = False

            if condition:
                self.grid[x_test,y_test,z]=[
                                            WorldTile.entry_point,
                                            [color.GREEN,color.BOLD]
                                            ]

                self.start = (x_test,y_test,z)
                self.logger.debug('\tEntry point set : {0}'.format((
                                                        x_test,y_test,z
                                                        )))
                break
            iterations += 1

        self.logger.debug('\tEntry point took {} attempts'.format(iterations))
        self.logger.debug('\tTook {}s'.format(time.clock()-start))

    def set_descent_point(self):
        """ Sets point to descend/ascend on each level """

        self.logger.info('[*] Setting descent points')
        start = time.clock()

        i = 0
        while i < self.dim_z: # Loop until bottom floor
            x_test = random.randint(0,self.dim_x-1)
            y_test = random.randint(0,self.dim_y-1)

            if i==0:
                tile_type = WorldTile.entry_point
            else:
                tile_type = WorldTile.ascent_point

            check_point = self.find_tile(i,tile_type)

            assert check_point, 'Tile Not Found! lvl {0}:{1}\n{2}'.format(
                                                            i,
                                                            tile_type,
                                                            self
                                                            )

            if self.calc_dist(check_point,(x_test,y_test))>=self.min_dist:
                # If the distance is acceptable, set the points
                # and move to next level :

                # Add a descent point in the grid template
                self.grid[x_test,y_test,i]=[
                                    WorldTile.descent_point,
                                    [color.CYAN,color.BOLD]
                                    ]
                self.logger.debug(
                       '\tDescent Point Set {0}'.format((x_test,y_test,i))
                       )

                # Add corresponding ascent point on the next floor
                self.grid[x_test,y_test,i+1]=[
                                    WorldTile.ascent_point,
                                    [color.RED,color.BOLD]
                                    ]
                self.logger.debug(
                       '\tAscent Point Set {0}'.format((x_test,y_test,i+1))
                       )
                i += 1

        self.logger.debug('\tTook {}s'.format(time.clock()-start))

    def path_avail_dirs(self,position,impediments,dest=None,rand=False):
        # Processes available directions, returns a random direction
        # if the random flag is passed, else returns the direction
        # list

        self.logger.debug('[*] Finding available directions')

        imp = ''.join(str(i) for i in impediments)
        self.logger.debug('\tImpediments : {}'.format(imp))

        p = position
        self.logger.debug('\tPosition : {}'.format(p))

        # Define directions
        north = [0,1]
        south = [0,-1]
        east = [1,1]
        west = [1,-1]

        if dest is not None:
            prefer_y = [True] if p[0]==dest[0] else [False]
            prefer_x = [True] if p[1]==dest[1] else [False]

            if p[0]<dest[0] and prefer_x: prefer_x.append(1)
            if p[0]>dest[0] and prefer_x: prefer_x.append(-1)
            if p[1]<dest[1] and prefer_y: prefer_y.append(1)
            if p[1]>dest[1] and prefer_y: prefer_y.append(-1)

            # Reduce compared value for more direct paths
            if random.randint(0,100)>30:
                apply_preference=True
            else:
                apply_preference=False

        # impediments will contain impassable vals
        # x-axis
        if p[0]+1>=self.dim_x:
            north.append(False)
        else:
            north.append(
                True if self.grid[p[0]+1,p[1],p[2]][0] not in imp else False
                )

        if p[0]-1<=0:
            south.append(False)
        else:
            south.append(
                True if self.grid[p[0]-1,p[1],p[2]][0] not in imp else False
                )

        # y-axis
        if p[1]+1>=self.dim_y:
            east.append(False)
        else:
            east.append(
                True if self.grid[p[0],p[1]+1,p[2]][0] not in imp else False
                )
        if p[1]-1<=0:
            west.append(False)
        else:
            west.append(
                True if self.grid[p[0],p[1]-1,p[2]][0] not in imp else False
                )

        dirs = [north,south,east,west]
        assert any(dirs),'Pathbuilder : No available moves!'

        if not rand:
            return dirs
        elif apply_preference and (prefer_x or prefer_y):
            if prefer_x[0]:
                self.logger.debug('\tPreferring x : {}'.format(prefer_x[1]))
                return 0,prefer_x[1]
            elif prefer_y:
                self.logger.debug('\tPreferring y : {}'.format(prefer_y[1]))
                return 1,prefer_y[1]
        else:
            # Randomly selects an available move and returns it
            while True:
                roll = random.randint(0,3)
                dirs = [north,south,east,west]
                if dirs[roll][2]:
                    if roll in [0,1]:
                        idx = 0
                        val = 1 if roll==0 else -1
                    else:
                        idx = 1
                        val = 1 if roll==2 else -1
                    break

            self.logger.debug('\tindex (x,y)= {} value= {}'.format(idx,val))
            return idx,val

    def calc_dist(self,pt1,pt2):
        x_term = pt1[0]-pt2[0]
        y_term = pt1[1]-pt2[1]
        return math.sqrt(x_term**2+y_term**2)

    def find_tile(self,z,tile_type):
        """ Looks for the given tile type on the requested floor """
        retval = False
        for y in range(self.dim_y):
            for x in range(self.dim_x):
                if tile_type==self.grid[x,y,z][0]:
                    retval = (x,y,z)

        return retval

    def set_exit_point(self):
        """ Sets exit point on the map edge, far enough from entry """

        valid_x = range(1,self.dim_x-1)
        valid_y = range(1,self.dim_y-1)
        max_attempts = 500
        this_attempt = 0

        self.logger.info('[*] Setting exit point')
        self.logger.debug('\tvalid_x range : {}'.format(valid_x))
        self.logger.debug('\tvalid_y range : {}'.format(valid_y))

        while True:
            x_test = random.randint(0,self.dim_x-1)
            y_test = random.randint(0,self.dim_y-1)
            if x_test in valid_x and y_test not in valid_y:
                condition = True
            elif y_test in valid_y and x_test not in valid_x:
                condition = True
            else:
                condition = False

            if condition:
                asc = self.find_tile(self.dim_z-1,WorldTile.ascent_point)

                assert asc,'Ascent point not found! {0}\n{1}'.format(
                                                            self.dim_z,
                                                            self)
                self.logger.debug('\tAscent point found : {}'.format(asc))
                test = (x_test,y_test,self.dim_z)
                if self.calc_dist(asc,test)>=self.min_dist:
                    self.grid[test]=[
                                    WorldTile.exit_point,
                                    [color.GREEN,color.BOLD]
                                    ]
                    self.end = test
                    self.logger.debug(
                           '\tExit Point Set {0}'.format(tuple(test)
                           ))
                    return True
                    break

            this_attempt += 1

            if this_attempt >= max_attempts:
                again = raw_input('Max attempts reached, continue(y)?')
                if again not in ['y','Y']:
                    return False
                    break
                else:
                    this_attempt = 0

    def build_paths(self):
        """ Builds paths of hallways to waypoints """

        waypoints_per_floor = ((self.dim_x+self.dim_y)/2)/2
        self.logger.debug(
            '\tWaypoint density : {0}'.format(waypoints_per_floor)
            )
        self.way_list = self.build_waypoints(waypoints_per_floor)

        for i in range(len(self.way_list)-1):
            way1 = self.way_list[i]
            way2 = self.way_list[i+1]

            # If the two waypoints are on the same floor,
            # connect them
            if way1[2]==way2[2]:
                self.logger.info('[*] Connecting {0} to {1}'.format(way1,way2))
                self.connect(way1,way2)

    def connect(self,pt1,pt2):
        """ Connects the two points with hallway tiles """

        tile_list = []  # List of tiles to be set
        self.history.append(pt1)    # Append to the history
        coord_list = list(pt1)  # create a mutable coord list

        max_loops = 35      # Max loops per leg
        this_loop = 0

        while True:
            # Pathbuilder exit conditions:
            if this_loop >= max_loops:
                self.logger.debug('\tMaximum steps for this leg (pathbuilder)')
                break
            if tuple(coord_list)==pt2:
                # Arrived at destination waypoint
                self.logger.debug('\tArrived at point {}'.format(pt2))
                break

            # Final leg detector - executes when a point is reached
            # on the same axis (x/y) and within 2 tiles.  Directly
            # connects to the endpoint
            if coord_list[0]==pt2[0] and abs(coord_list[1]-pt2[1])<3:
                idx = 1     # axis of motion = x
                rng = coord_list[1]-pt2[1]
            elif coord_list[1]==pt2[1] and abs( coord_list[0]-pt2[0])<3:
                idx = 0     # axis of motion = x
                rng = coord_list[0]-pt2[0]
            else:
                rng = False

            if rng:
                self.logger.debug('\tDestination point in range')
                for n in range(rng):
                    coord_list[idx]+=n
                    tile_list.append(tuple(coord_list))
                break
            # If not the final leg, randomly select a direction
            idx,val = self.path_avail_dirs(
                                coord_list,
                                ['E','U','D','3'],
                                pt2,
                                True)
            coord_list[idx]+=val
            tile_list.append(tuple(coord_list))
            this_loop +=1

        # Fill the resulting point list with hallways in the grid
        for tile in tile_list:
            try:
                if self.grid[tile][0]==WorldTile.wall:
                    self.grid[tile]=[
                                    WorldTile.hallway,
                                    [color.BLUE,color.BOLD]
                                    ]
            except KeyError:
                if not self.silent:
                    self.logger.error('[*] Invalid tile specified!')
                self.logger.debug('Tile value : {}'.format(tile))
                continue

    def build_waypoints(self,w):
        retval = []
        for z in range(self.dim_z+1):
            # Set starting waypoint for the floor
            if z == 0:
                retval.append(self.start)
            else:
                retval.append(self.find_tile(z,WorldTile.ascent_point))

            # Fill other waypoints
            dbg_string = 'Floor {} waypoints :\n\t'.format(z)
            for way in range(w):
                x = random.randint(1,self.dim_x-1)
                y = random.randint(1,self.dim_y-1)

                if len(retval)%4==0:
                    dbg_string += '{}\n\t'.format((x,y,z))
                else:
                    dbg_string += '{0},'.format((x,y,z))

                retval.append((x,y,z))
            dbg_string = dbg_string[:-1]
            self.logger.debug(dbg_string)

            # Set ending waypoint for the floor
            if z == self.dim_z:
                retval.append(self.end)
            else:
                retval.append(self.find_tile(z,WorldTile.descent_point))
        return retval

    def find_path_ends(self,z):
        """ Returns the endpoints for the given floor """
        if z == 0:
            start = self.find_tile(z,WorldTile.entry_point)
            end = self.find_tile(z,WorldTile.descent_point)
        elif z == self.dim_z:
            start = self.find_tile(z,WorldTile.ascent_point)
            end = self.find_tile(z,WorldTile.exit_point)
        else:
            start = self.find_tile(z,WorldTile.ascent_point)
            end = self.find_tile(z,WorldTile.descent_point)

        return start, end

    def gen_feature(self,feature):
        if feature=='s_curve':
            pass
        elif feature=='dead_end':
            pass

    def build_rooms(self):
        """ Builds rooms off of the paths """

        for z in range(0,self.dim_z+1):
            start, end = self.find_path_ends(z)
            for pt in (start,end):
                self.create_room(WorldTile.dungeon,pt,1)

        for way in self.way_list:
            self.create_room(WorldTile.dungeon,way)


    def create_room(self,fill,center,size=None,color=None):
        """ Creates a rectangle in the approximate size passed, None = random """

        if size is None:
            size = random.randint(1,2)

        # Only allow overwrite of appropriate tiles
        overwrite_allowed = (
                            WorldTile.wall,
                            WorldTile.hallway,
                            WorldTile.door
                            )

        # Replaces tile contents in a square around the center with fill
        for x_offset in range(-size,size+1):
            for y_offset in range(-size,size+1):

                # Eliminate values outside the grid
                if center[0]+x_offset > self.dim_x-1 or center[0]+x_offset < 0:
                    x_offset=0
                if center[1]+y_offset > self.dim_y-1 or center[1]+y_offset < 0:
                    y_offset=0

                pt = (center[0]+x_offset,center[1]+y_offset,center[2])
                for tile in overwrite_allowed:
                    if tile==self.grid[pt][0]:
                        self.grid[pt]=[fill,color]

    def test_paths(self):
        """ Confirms each waypoint is reachable """

        for z in range(self.dim_z+1):
            # Create the graph, impediments are walls(0) and locked doors(L)

            imp = []

            this_floor = [None for y in range(self.dim_y)]
            for y in range(self.dim_y):
                this_floor[y]=[None for x in range(self.dim_x)]
                for x in range(self.dim_x):
                    this_floor[y][x]=self.grid[x,y,z][0]

            graph = GraphGrid(this_floor)

            # Default impediments are wall(0) and locked doors(L)
            imp=[(a,b) for a,b,c in self.grid if self.grid[a,b,z][0] in [0,'0','L']]

            # Set the list of impassable points
            graph.impassable = imp

            # Set the floor start and end points
            start,end = self.find_path_ends(z)

            self.logger.info('[*] Testing the path from {} to {}'.format(start,
                                                                         end))

            # Initialize the path tester, as a_star for best path
            path_tester=Pathfinder(Pathfinder.gb_first)
            path_tester.g = graph
            path_tester.start = start[:2]
            path_tester.dest = end[:2]
            path = path_tester.execute()

            if not path:
                self.logger.error("Invalid pathfinding algorithm")
            else:
                for (x,y) in path:
                    val=path[x,y]
                    if val is not None:
                        if self.grid[x,y,z][0] not in ['U','D','S','E']:
                            self.grid[val[0],val[1],z][1]=[color.WHITE_ON_BLUE]
                #for x,y in path[1]:
                    #print 'coord={}'.format(x)
                    #print 'score={}'.format(y)
                    #if self.grid[x,y,z][0] not in ['U','D','S','E']:
                        #self.grid[x,y,z][1]=[color.WHITE_ON_BLUE]

    def color_test(self):
        """ prints table of formatted text format options """

        for style in xrange(8):
            for fg in xrange(30,38):
                s1 = ''
                for bg in xrange(40,48):
                    fmt = ';'.join([str(style), str(fg), str(bg)])
                    s1 += '\x1b[%sm %s \x1b[0m' % (fmt, fmt)
                print s1
            print '\n'

class CLInvoker(object):
    """ Class to handle command line execution """

    def __init__(self):

        if '-d' in sys.argv or '--debug' in sys.argv or \
           '-v' in sys.argv or '--verbose' in sys.argv:

            log_level = logging.DEBUG
        else:
            log_level = logging.INFO

        self.logger = logger(__name__,log_level)
        self.logger.info('[*] Command-line invoker engaged')

        try:
            self.handle_args()
            start = time.clock()
            self.world = WorldGenerator(
                        self.args.debug,self.args.silent,self.args.random,
                        self.args.fpath,self.args.conf,self.args.xdim,
                        self.args.ydim,self.args.zdim,self.args.elastic,
                        self.args.verbose,self.logger,self.args.path
                        )
            self.logger.debug('\tWorld generation took {}s'.format(
                                                        time.clock()-start
                                                        ))
            while True:
                self.menu()

        except (KeyboardInterrupt,SystemExit):
            sys.exit(0)

    def menu(self):
        """ Main menu """

        post = "done!" if self.world.post_done else "not done"

        menu_items = [
                ('Show [m]ap','m',self.show_map),
                ('[C]heck level paths ({})'.format(post),'c',
                                                    self.world.test_paths),
                ('[R]egenerate','r',self.regenerate),
                ('[S]ave ({})'.format(self.args.fpath),'s',self.save_map),
                ('[Q]uit','q',sys.exit)
                ]

        for n in range(len(menu_items)):
            print '{}. {}'.format(n,menu_items[n][0])

        ch = raw_input('Selection > ')

        if ch.lower() not in [item[1] for item in menu_items]:
            print 'Invalid selection : ', ch.lower()
            raw_input('Press any key to continue (Ctrl+C exits)\n')
        else:
            for item in menu_items:
                if ch.lower()==item[1]:
                    item[2]()

    def show_map(self):
        print self.world

    def regenerate(self):
        try:
            self.world = WorldGenerator(
                       self.args.debug,self.args.silent,self.args.random,
                       self.args.fpath,self.args.conf,self.args.xdim,
                       self.args.ydim,self.args.zdim,self.args.elastic,
                       self.args.verbose,self.logger,self.args.path
                       )
        except TypeError:
            self.world = WorldGenerator()

    def save_map(self):
        """ Saves the map template to a python file, as a 2-tuple """

        self.logger.info('[*] Saving map template')

        o = 'map_template = (\n'
        for z in range(int(self.args.zdim)):
            o += '  (\n'
            for y in range(int(self.args.ydim)):
                o += '    ('
                tmp = ''
                for x in range(int(self.args.xdim)):
                    tmp += '{},'.format(self.world.grid[x,y,z][0])
                o += tmp[:-1]
                o += '),\n'
            o += '  ),\n'

        o += ')\n'

        try:
            with open(self.args.fpath,'w') as outfile:
                outfile.write(o)
        except:
            self.logger.error('\tFile write failed to {} '.format(
                                                   self.args.fpath
                                                   ))
        else:
            self.logger.debug('\tFile written successfully to {}'.format(
                                                        self.args.fpath
                                                        ))
            self.logger.debug('\tList variable = map_template')

    def handle_args(self):

        parser = argparse.ArgumentParser()
        self.logger.info('[*] Handling command line arguments')

        # Arg_list : [0]=short arg, [1]=long arg, [2]=help msg,
        #            [3]=store_true/false, [4]=default, [5]=nargs
        arg_list =  [
            ("-d","--debug","enable debug mode",'store_true'),
            ("-s","--silent","silent mode (no output)",'store_true'),
            ("-r","--random","generates a randomized map",'store_true'),
            ("-f","--fpath","specify output file",None,'world_gen_output.py',str),
            ("-c","--conf","specify conf file",None,'world_gen.conf',str),
            ("-x","--xdim","map x dimension",None,30,int),
            ("-y","--ydim","map y dimension",None,20,int),
            ("-z","--zdim","map floor depth",None,3,int),
            ('-e','--elastic','specify flexible dimensions',None,3,int),
            ('-v','--verbose','enable verbose messages','store_true'),
            ('-p','--path','perform automatic map path validation','store_true')
            ]

        # Parse Flags (boolean)
        self.logger.debug('\tAdding boolean flags')
        for f in [arg for arg in arg_list if arg[3] is not None]:
            parser.add_argument(f[0],f[1],help=f[2],action=f[3])

        # Parse Parameters (values)
        self.logger.debug('\tAdding parameters')
        for p in [arg for arg in arg_list if arg[3] is None]:
            parser.add_argument(p[0],p[1],
                                help=p[2],
                                default=p[4],
                                type=p[5])

        self.logger.debug('\tParsing arguments')
        self.args=parser.parse_args()

        # Handle randomization here, if enabled
        if self.args.random:
            self.args.xdim = random.randint(30,50)
            self.args.ydim = random.randint(20,40)
            self.args.zdim = random.randint(3,5)

if __name__=='__main__':
    CLInvoker()
