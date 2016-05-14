#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import random
import pokeygame
from pokeygame import Skill

easy_list = [
            CombatSkill,
            StealthSkill,
            MagicSkill,
            MapSkill
            ]

class CombatSkill(Skill):

    """ Combat skills, botched roll temporarily reduces defense """

    def __init__(self):
        self.name = 'Punch'
        self.type = Skill.combat_type
        self.level = 1

class StealthSkill(Skill):

    """ Stealth skills, botched roll temporarily reduces attack """

    def __init__(self):
        self.name = 'Stab'
        self.type = Skill.stealth_type
        self.level = 1

class MagicSkill(Skill):

    """ Magic skills, botched roll temporarily reduces focus """

    def __init__(self):
        self.name = 'Flare'
        self.type = Skill.magic_type
        self.level = 1

class MapSkill(Skill):

    """ Map and navigation skills, no botched effects """

    def __init__(self):
        self.name = 'View Map'
        self.type = Skill.general_type
        self.level = None
