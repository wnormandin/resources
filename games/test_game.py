#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import pokeyworks
import pokeygame

# test_game must be in the same dir as these resources :
import mobs,players,items,tiles

class TestGame(pokeygame.PokeyGame)
    """ Test Game application for the PokeyGame console framework """
    
    def __init__(self,name):
        """ Custom __init__ for extended options """
        
        super(TestGame,self).__init__(name)
