#!/usr/local/bin/python2.7
# -*- coding: utf-8 -*-

import os
import sys
import time
import argparse

# Colorize console output
from pokeyworks import Color, color_wrap
# Configuration base class
from pokeyworks import PokeyConfig
from pokeyworks import resource_path


class AppConfig():

    def __init__(self):
        self.parse_args()
        self.cwd = os.getcwd()  # Grab the script execution directory
        self.mydir, self.mypath = os.path.split(__file__)

        if not self.args.skip:
            self.print_app_headers()

        self.cfg = None
        self.highlight = Color.BLUE

        # Menu option groups :
        #       {
        #       label:,
        #       hotkey_char:
        #       hotkey_color:
        #       method:
        #       method_args:[]
        #       menu_action:
        #       }
        #       menu_actions : None = Remain, True = Previous, False = Quit

        self.submenu_1 = [
            {
            'label':'\nView options',
            'hotkey_char':'V',
            'hotkey_color':self.highlight,
            'method':self.print_config,
            },
            {
            'label':'Add an option',
            'hotkey_char':'A',
            'hotkey_color':self.highlight,
            'method':self.add_option,
            },
            {
            'label':'Edit an option',
            'hotkey_char':'E',
            'hotkey_color':self.highlight,
            'method':self.edit_option,
            },
            {
            'label':'Remove an option',
            'hotkey_char':'R',
            'hotkey_color':self.highlight,
            'method':self.remove_option,
            },
            {
            'label':'Write config',
            'hotkey_char':'W',
            'hotkey_color':self.highlight,
            'method':self.write_config,
            },
            {
            'label':'Back',
            'hotkey_char':'B',
            'hotkey_color':Color.RED,
            'menu_action':True
            }
            ],
        self.convert_menu = [
            {
            'label':'\nConvert (JSON <-> YAML)',
            'hotkey_char':'C',
            'hotkey_color':self.highlight,
            'method':self.file_convert,
            },
            {
            'label':'Encode (JSON|YAML -> base64 JSON)',
            'hotkey_char':'E',
            'hotkey_color':self.highlight,
            'method':self.file_convert,
            'method_args':PokeyConfig.encoded
            },
            {
            'label':'Back',
            'hotkey_char':'B',
            'hotkey_color':Color.RED,
            'menu_action':True
            }
            ],
        self.main_menu = [
            {
            'label':'\nOpen a file',
            'hotkey_char':'O',
            'hotkey_color':self.highlight,
            'method':self.file_select,
            },
           # {
           # 'label':'New config file',
           # 'hotkey_char':'N',
           # 'hotkey_color':self.highlight,
           # 'method':self.create_config,
           # },
            {
            'label':'Convert a file',
            'hotkey_char':'C',
            'hotkey_color':self.highlight,
            'method':self.go_to_submenu,
            'method_args':self.convert_menu
            },
            {
            'label':'Quit',
            'hotkey_char':'Q',
            'hotkey_color':Color.RED,
            'menu_action':False
            }
            ]

        while True:
            # Main application execution loop
            try:
                self.menu_queue = [self.main_menu]

                # If a file argument is passed, load it
                # and move to the config submenu
                if self.args.file != '':
                    self.menu_queue.append(self.submenu_1)
                    print self.args.file
                    self.open_file()

                self.menu()
            except SystemExit,KeyboardInterrupt:
                ch = raw_input('Really quit? ')
                if ch.upper()=='Y':
                    sys.exit(0)
                else:
                    continue
            else:
                ch = raw_input("Exit? ")
                if ch.upper() == 'Y':
                    sys.exit(0)

    def file_convert(self,out_type=None):

        infile = raw_input("Specify an input file (q quits) > ")
        infile = self.check_cwd(infile)

        if infile.upper()=='Q':
            return

        if infile.endswith('.yml'):
            self.cfg = PokeyConfig(infile,PokeyConfig.yaml)
        elif infile.endswith('.json'):
            self.cfg = PokeyConfig(infile)
        elif infile.endswith('.cfg'):
            self.cfg = PokeyConfig(infile,PokeyConfig.encoded)
        else:
            print 'Invalid file format : {}'.format(infile)
            return

        if out_type==None and self.cfg.loaded_type==PokeyConfig.json:
            out_type=PokeyConfig.yaml
        elif out_type==None and self.cfg.loaded_type==PokeyConfig.yaml:
            out_type=PokeyConfig.json

        self.cfg.convert_config(out_type)

    def check_cwd(self,infile,rel=True):

        # Relative flag will be handled as follows :
        #
        # rel = relative to the execution path
        #
        # True = base the file path on the execution directory 
        #   - Examples : configuration input and output files
        # False = base the file path on the configure.py script location
        #   - Examples : configure.py resources
        # None = base the file path on the pokeyworks.py directory
        #   - Examples : accessing other pokeycode resources

        script_dir = os.path.dirname(__file__)

        if self.cwd != script_dir and rel=:
            path_base, fname = os.path.split(infile)
            retval = os.path.join(self.cwd,fname)
        else:
            retval = infile

        return retval

    def go_to_submenu(self,submenu):
        self.menu_queue.append(submenu)

    def parse_args(self):
        parser = argparse.ArgumentParser(description='Process PokeyConfig files',
                            epilog='To convert, pass a legacy file and conversion \
                            format, you will be prompted to choose a format.'
                            )
        parser.add_argument('-k','--skip',help='Skip the intro banner',
                            action='store_true')
        parser.add_argument('-d','--debug',help='Enable debugging messages',
                            action='store_true')
        parser.add_argument('-f','--file',help='Specify a file',
                            default='')
        parser.add_argument('-c','--convert',
                            help='w/--file, convert file format, 1=json,2=yaml,3=base64',
                            default=PokeyConfig.json, type=int,nargs=1)
        self.args = parser.parse_args()

    def menu(self):
        # Prints menu options and handles user selections
        # menu_queue is a LIFO queue

        while True:
            current_menu = self.menu_queue[-1]
            selection_msg = "\nSelection > "
            valid_selections = [i['hotkey_char'] for i in current_menu]

            for item in current_menu:
                # Apply color to hotkey character
                hotkey = color_wrap(item['hotkey_char'],item['hotkey_color'])
                # Populate text
                text = list(item['label'])
                # Replace hotkey character with colorized value
                text[text.index(item['hotkey_char'])]=hotkey
                print ''.join(text)

            ch = raw_input(selection_msg)

            if ch.upper() not in valid_selections:
                selection_msg = '\nInvalid Selection > '
            else:
                selection_msg = '\nSelection > '

                for item in current_menu:
                    if ch.upper()==item['hotkey_char']:
                        run_method = item.get('method')
                        args = item.get('method_args')
                        action = item.get('menu_action')
                        if run_method is not None:
                            if args is not None:
                                try:
                                    run_method(*args)
                                    break
                                except TypeError:
                                    run_method(args)
                                    break
                            else:
                                run_method()
                                break
                        if action is not None:
                            if not action:
                                # Exit the app with success msg
                                sys.exit(0)
                            else:
                                self.menu_queue.pop()
                        else:
                            # Add the current menu to the queue to stay
                            self.menu_queue.append(current_menu)

    def print_app_headers(self):
        header_path = self.check_cwd('app_header.txt')
        with open(header_path, 'r') as f:
            data = f.readlines()

        slp_time = 1.0
        for row in data:
            time.sleep(slp_time)
            print row.rstrip()
            slp_time = slp_time - slp_time/7

    def print_config(self):
        print '\nLoaded Options :'
        for key in self.cfg.conf_dict:
            print ' [{}] = {}'.format(key,self.cfg.conf_dict[key])

    def add_option(self):
        key = raw_input('Option : ')
        val = raw_input('Value  : ')
        self.cfg.conf_dict[key]=val

    def edit_option(self):
        while True:
            self.print_config()
            print '\n[Edit Option]'
            key = raw_input('Selection (q quits) > ')
            if key.upper() in ['Q','QUIT','EXIT']:
                break
            if key in self.cfg.conf_dict:
                self.cfg.conf_dict[key] = raw_input('Value > ')
            else:
                msg = 'Option {} does not exist, create it? '.format(key)
                ch=raw_input(msg)
                if ch.upper() in ['Y','YES']:
                    self.cfg.conf_dict[key]=raw_input('Value > ')

    def remove_option(self,opt=None):
        if opt is not None and opt in self.cfg.conf_dict:
            del self.cfg.conf_dict[opt]
            return
        elif opt is not None:
            print "Option not in list!"
        self.print_config()
        print '\n[Remove Option]'
        key = raw_input('Selection (q quits) > ')
        if key.upper() in ['Q','QUIT','EXIT']:
            return
        elif key in self.cfg.conf_dict:
            del self.cfg.conf_dict[key]
            return
        print 'Option not found!'

    def write_config(self):
        self.cfg.write_config()

    def open_file(self):
        fname = self.args.file
        print 'Opening {}'.format(fname)
        if fname.endswith('.json'):
            self.cfg = PokeyConfig(fname)
        elif fname.endswith('.yml'):
            self.cfg = PokeyConfig(fname,PokeyConfig.yaml)
        else:
            self.convert_file(fname)

    def file_select(self):
        fname = raw_input("Enter a path : ")
        try:
            filesize = os.stat(fname).st_size
            print fname, filesize
            ch = raw_input("Load this config? ")
            if ch.upper() in ['Y','YES']:
                if fname.endswith('.json'):
                    self.cfg = PokeyConfig(fname)
                elif fname.endswith('.yml'):
                    self.cfg = PokeyConfig(fname,2)
                elif fname.endswith('.cfg'):
                    self.cfg = PokeyConfig(fname,3)
                else:
                    raise AssertionError("Unknown file type : {}".format(fname))
            self.menu_queue.append(self.submenu_1)
        except OSError:
            print "File not found! {}".format(fname)

    def create_config(self):
        fname = raw_input("Config file name : ")
        if fname.endswith(".json"):
            args = [fname]
        elif fname.endswitch(".yml"):
            args = [fname,2]
        else:
            print "Invalid file type : {}".format(fname)
            return False
        try:
            with open(fname,'a') as touchfile:
                #Touch!
                pass
        except IOError:
            print "Unable to stat file : {}".format(fname)
            return False
        self.cfg = PokeyConfig(*args)
        ch = raw_input("Config file created!  Add options? ")
        if ch.upper() in ['Y','YES']:
            return 1    # Need to catch this and move to submenu 1
        else:
            return 0

    def convert_file(self,fpath):
        if self.cfg.loaded_type == PokeyConfig.json:
            self.cfg.fpath = self.cfg.convert_file_path(fpath,'.yml')
            self.cfg.save_yaml(self.cfg.fpath,self.cfg.conf_dict)
            self.cfg.loaded_type = PokeyConfig.yaml
        elif self.cfg.loaded_type == PokeyConfig.yaml:
            self.cfg.fpath = self.cfg.convert_file_path(fpath,'.json')
            self.cfg.save_json(self.cfg.fpath,self.cfg.conf_dict)
            self.cfg.loaded_type = PokeyConfig.json
        else:
            raise AssertionError("Unknown type : {}".format(self.cfg.loaded_type))

        print "{} converted to {}".format(fpath,self.cfg.fpath)

if __name__=='__main__':
    AppConfig()
