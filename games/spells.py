#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import pokeygame
from tiles import WorldTile

class Spell(object):

    """ Generic Spell Class """

    # Spell Types
    offensive = 0
    status = 1
    seal = 2

    # Spell Elements
    fire = 0
    ice = 1
    poison = 2

    def __init__(
                self,
                immediate = False,  # If True cast spell immediately
                sp_type = None,     # Spell cast type
                sp_elem = None,     # Spell element
                sp_trigger = None,  # Spell trigger events
                counter = 1,        # Spell remaining casts
                dmg_range = (5,10)  # Possible damage range 
                ):

        if self.immediate:
            self.cast()

    def validate_target(self,t):

        assert self.target is not None, 'No Target Specified'

        assert isinstance(self.target, t), \
                'Invalid spell target : {}'.format(self.target)

        if t == PokeyGame.Entity:
            assert self.target.living, 'Spell target is dead'

        if self.sp_type == Spell.offensive:
            assert self.sp_elem is not None, 'No offensive spell element set'

    def trigger(self,event):

        # Process trigger events

        if self.sp_trigger == event:
            self.cast()

    def cast(self):

        if self.sp_type == Spell.offensive:

            # Ensure the spell target is eligible to receive damage
            self.validate_target(PokeyGame.Entity)
            self.damage_target()

        elif self.sp_type == Spell.status:
            # Ensure the spell target can be effected
            self.validate_target(PokeyGame.Entity)
            self.target.status_effect(self.effect)

        elif self.sp_type == Spell.seal:
            # Ensure the seal target can be sealed
            self.validate_target((
                                pokeygame.Trap,
                                WorldTile.Door,
                                WorldTile.Chest
                                ))
            self.target.apply_seal(self)

        return self.applied()

    def applied(self):
        assert isinstance(self.counter,int), 'Invalid counter!'
        if self.counter > 0:
            self.counter -= 1
            return self
        else:
            return None

    def random_spell(self,sp_type=None):
        assert sp_type is not None, 'Spell type required for random selection'


    def damage_target(self):
        self.target.apply_spell_damage(self.sp_elem,self.dmg_range)
class Paralyze(Spell):

    """ Apply the Paralyze status effect """

    def __init__(self,target,turns):

        assert isinstance(turns, int), 'Turn count must be integer!'
        self.target = target

        Super(Paralyze,self).__init__(
                                True,           # Immediately cast
                                Spell.status,
                                None, None,
                                turns,
                                None
                                )

class FlameBolt(Spell):

    """ Immediately cast a flame damage spell """

    def __init__(self,target,dmg_range):
        self.target = target
        Super(FlameBolt,self).__init__(
                                True,           # Immediately cast
                                Spell.offensive,
                                Spell.fire,
                                None, 1,
                                dmg_range
                                )

class ExplosiveSeal(Spell):

    """ Fire-Based damage seal for doors, chests, and traps """

    def __init__(self):
        self.sp_type = Spell.seal,
        self.sp_elem = Spell.fire,

        # Trigger event in Player so that only
        # players can trigger seals
        self.sp_trigger = Player.trigger_seal,
        self.dmg_range = (5,15)
        self.counter = 1

        # Skip the Super call for this type
