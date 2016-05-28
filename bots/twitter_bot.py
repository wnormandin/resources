#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import sys
import pokeybots

#import imp
#pokeybots = imp.load_source('pokeybots','/home/pokeybill/python/projects/pokey/pokeybots.py')

#from pokeybots import PokeyTwit

twit = pokeybots.PokeyTwit()
if twit.exit_status==1:
    print "Error in twitter_bot execution"

sys.exit(twit.exit_status)   
