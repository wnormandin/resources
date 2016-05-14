#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import subprocess
import time
import sys
import argparse
import logging
import pokeyworks as fw
from pokeyworks import Daemon

class MobileDaemon(Daemon):

    """ Daemon process manager """

    def run(self):
    	while True:
            time.sleep(5)

class MonitorApplication(object):

    """ Monitors for mobile devices in the argument list """

    def __init__(self):

        self.logger = fw.setup_logger('MobileMonitor',logging.DEBUG)
        self.logger.info("[*] Local network keychain monitor engaged")

        self.pidpath = '/tmp/MobileDaemon.pid'
        self.logger.info("\tPID file path : {}".format(self.pidpath))

        self.daemon = MobileDaemon(self.pidpath)

        self.handle_args()
        if self.args.mac:
            self.logger.info("\tScanning for MAC {}".format(self.args.mac))
        self.handle_actions()

    def handle_actions(self):
        if self.args.start and self.args.mac:
            self.daemon.start()
        elif self.args.restart and self.args.mac:
            self.daemon.restart()
        elif self.args.stop:
            self.daemon.stop()
        else:
            raise AssertionError("Invalid argument, use --help")
            sys.exit(2)
        sys.exit(0)

        # Daemon takes over
        while True:
            time.sleep(5)
            p = subprocess.Popen(
                        "arp-scan -l | grep {}".format(self.mac),
                        stdout = subprocess.PIPE,
                        shell = True
                        )
            out, err = p.communicate()
            p_stat = p.wait()
            if out:
                self.logger.info("[*] MAC {} detected".format(self.args.mac))
                subprocess.call(["xscreensaver-command","-deactivate"])

    def handle_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument(
                            "-s",
                            "--start",
                            help="starts monitor",
                            action='store_true'
                            )
        parser.add_argument(
                            "-e",
                            "--stop",
                            help="stops monitor",
                            action="store_true"
                            )
        parser.add_argument(
                            "-r","--restart",
                            help="restarts the monitor",
                            action="store_true"
                            )
        parser.add_argument(
                            "-d","--debug",
                            help="enable debug messaging",
                            action="store_true"
                            )
        parser.add_argument(
                            "-m","--mac",
                            help = "specify the MAC to scan for",
                            default=False,
                            nargs=1
                            )
        self.args = parser.parse_args()

if __name__ == '__main__':
    MonitorApplication()
