#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import pokeygame

class WorldTile(object):

    """ Class to contain world tile objects """

    wall = '0'
    hallway = '1'
    door = '2'
    dungeon = '3'
    shop = '4'
    boss = '5'

    entry_point = 'S'
    descent_point = 'D'
    exit_point = 'E'
    ascent_point = 'U'

    tile_set = [wall,hallway,door,dungeon,shop,boss,
                entry_point,descent_point,exit_point,
                ascent_point]

    def __init__(self,tile_name,tile_type,**kwargs):
        self.tile_name = tile_name
        self.tile_type = tile_type
        assert self.tile_type in WorldTile.tile_set,'Invalid Tile Type'

        # kwarg defaults
        for pair in [
                    ('eligibles',{}),   # Eligible item/mob/trap types   
                    ('visible',False),  # Sets tile map visibility
                    ('explored',False), # Tile explored flag
                    ('spawn_rate',False),# General contents spawn rate
                    ('locked',False),   # Locked status (doors only)
                    ('mobs',[]),        # List of contained mobs
                    ('corpses',[]),     # List of contained corpses
                    ('items',[]),       # List of contained items
                    ('traps',[]),        # List of contained traps
                    ('description',''), # Tile description
                    ('traversable',True) # Traversable flag
                    ]:
            try:
                setattr(self,pair[0],kwargs[pair[0]])
            except:
                setattr(self,pair[0],pair[1])

        # Only allow locking if the tile is a door
        if self.tile_type != WorldTile.door:
            assert not self.locked, 'Invalid tile to lock:{0}'.format(
                                                            self.tile_type
                                                            )

        self.tile_initialize()

    def tile_initialize(self):
        for item in ['mobs','items','traps']:
            self.gen(item)

    def gen(self,tile_content):
        for item_type in self.eligibles:
            if item_type==tile_content:
                possibles = self.eligibles[item_type]

        self.level = 10
        item_list = getattr(self,item_type)
        succ,bonus = RandomRoll(self,self,self.spawn_rate)

        if succ and bonus:
            repetitions = 2
        elif succ:
            repetitions = 1
        else:
            repetitions = 0

        while repititions > 0:
            # Instantiates and appends the item_type
            item_list.append(possibles[random.randint(len(possibles))]())
            repetitions -= 1

class Dungeon(WorldTile):

    """ Generic dungeon room tiles """

    def __init__(self):
        spwn = 0.25
        desc = "A dungeon room"
        tile_name = "Dungeon"
        tile_type = WorldTile.dungeon

        super(Dungeon,self).__init__(
                                tile_name,
                                tile_type,
                                spawn_rate=spwn,
                                description=desc
                                )

class BossRoom(WorldTile):

    """ Designates the room where the boss will spawn, lowest level """

    def __init__(self):
        spwn = 0
        desc = "Room with a big boss in it"
        tile_name = "Boss Room"
        tile_type = WorldTile.boss

        super(BossRoom,self).__init__(
                                    tile_name,
                                    tile_type,
                                    spawn_rate=spwn,
                                    description=desc
                                    )

class Door(WorldTile):

    """ Generic Door Tile """

    def __init__(self):
        spwn = 0
        desc = 'A door'
        tile_name = "A doorway"
        tile_type = WorldTile.door

        super(Door,self).__init__(
                                tile_name,
                                tile_type,
                                spawn_rate=spwn,
                                description=desc,
                                locked=self.locked
                                )

    def toggle_locked(self,opt=None):
        if opt is not None:
            if self.locked != opt:
                self.locked = opt
        else:
            self.locked = not self.locked

class MagicDoor(Door):

    """ Doorway sealed by magic """

    def __init__(self,spell=None):
        self.toggle_locked(True)
        self.seal_door(spell)
        super(MagicDoor,self).__init__()

    def seal_door(self,spell=None):
        if spell is not None:
            self.seal=spell
        else:
            self.seal=random_seal()
class LockedDoor(Door):

    """ Doorway to a locked room """

    def __init__(self):
        self.locked=True
        super(LockedDoor,self).__init__()

class Hallway(WorldTile):

    """ Generic Hallway Tile """

    def __init__(self):
        kwargs = {
                'spawn_rate':10,
                'eligibles':{
                    'mobs':[mobs.GeneralMob],
                    'items':[items.GeneralItem],
                    'traps':[traps.GeneralTrap]
                    },
                'description':'A Generic Hall.  Period'
                }

        tile_name = 'A generic hall'
        tile_type = WorldTile.hallway

        super(Hallway,self).__init__(tile_name,tile_type,**kwargs)

class Wall(WorldTile):

    """ Generic, impassable wall """

    def __init__(self):
        args = {
                'traversable':False
                }
        tile_name = 'A wall'
        tile_type = WorldTile.wall

        super(Wall,self).__init__(tile_name,tile_type,**kwargs)

