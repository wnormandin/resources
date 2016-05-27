#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import mechanize
import urlparse
import random
import signal
import socket
import time
from  multiprocessing import Process, Pipe
import argparse
import os
import operator

def parse_arguments():

    parser = argparse.ArgumentParser()

    parser.add_argument('url',type=str,help='The URL to crawl')
    parser.add_argument('-v','--vary',action='store_true',
                help='vary the user-agent')
    parser.add_argument('-d','--debug',action='store_true',
                help='enable debug (verbose) messages')
    parser.add_argument('-p','--procs',type=int,default=4,
                choices=range(1,6),help='Concurrent processes (max 5)')
    parser.add_argument('-r','--report',action='store_true',
                help='display post-execution summary')
    parser.add_argument('--ua',type=str,
                help='specify a user-agent (overrides -v, def=firefox)')
    parser.add_argument('--gz',action='store_true',
                help='accept gzip compression (experimental)')
    parser.add_argument('--robots', action='store_true',
                help='honor robots.txt directives')
    parser.add_argument('--maxtime',type=int,default=20,
                help='Max run time in seconds')
    parser.add_argument('--verbose',action='store_true',
                help='displays all header and http debug info')

    return parser.parse_args()

class Stats:

    """ Stores various counters/convenience methods for reporting """

    def __init__(self):
        self.refresh()

    def refresh(self):
        # re-initialize each counter
        self.crawled_count = 0
        self.err = {}
        self.times = []

    def crawled(self,count):
        # increment the crawled_count
        self.crawled_count += count

    def time(self,times):
        # add times to the list for averaging
        self.times.extend(times)

    def error(self,deets):
        # increment each  error encountered
        # deets['url], deets['error']
        try:
            self.err[deets['error']][0] += 1
        except:
            self.err[deets['error']][0] = 1
        self.err[deets['error']].append(deets['url'])

def return_init(cls):

    # Allows returns other than the class instance
    def wrapper(args,):

        instance = cls(args,)
        return instance.retval

    return wrapper

#@return_init
class Spider:

    """ Spider superclass, contains all essential methods """

    def __init__(self,prms):
        # Takes any argument-containing namespace
        args,c_conn = prms
        if args.debug:
            print "Spider {} spawned".format(os.getpid())
        self.args = args
        self.cached_ips = {}
        self.history = []
        self.browser = prep_browser(args)
        self.url = self.prep_url(args.url)
        self.ip = self.dig(urlparse.urlparse(self.url).hostname)
        self.stats = {'times':[],'crawled':0,'err':[]}

        # Grab the current worker name
        self.name = 'Worker ({})'.format(
                    os.getpid()
                    )

        # Start the crawl
        try:
            self.get_links(self.url)
        except:
            c_conn.send(self.stats)
            raise
        finally:
            c_conn.send(self.stats)

    def prep_url(self,url):
        return 'http://'+url if 'http' not in url else url

    def dig(self,dom):
        if dom in self.cached_ips: return self.cached_ips[dom]
        self.cached_ips[dom] = ip = socket.gethostbyname(dom)
        return ip

    def get_links(self, url):
        print '{} : Crawling '.format(self.name), url
        start = time.clock()
        req = self.browser.open(url)
        self.stats['crawled']+=1
        self.stats['times'].append(time.clock()-start)
        for link in self.browser.links():
            if time.clock()-args.start >= args.maxtime:
                break
            if link.absolute_url not in self.history:
                ln = link.absolute_url
                dom = urlparse.urlparse(ln).hostname
                if dom and self.ip == self.dig(dom):
                    self.history.append(ln)
                    try:
                        self.get_links(ln)
                    except Exception as e:
                        if self.args.debug:
                            print '{} : '.format(ln),str(e)
                        self.stats['err'].append(
                            { 'error': str(e),'url':ln }
                            )

def prep_browser(args):

    # Defaults :
    b = mechanize.Browser()
    b.set_handle_robots(args.robots)
    b.set_handle_gzip(args.gz)
    b.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(),max_time=1)
    ua = 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) ' \
         + 'Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1'

    # With the user-agent vary option, substitute your own ua strings
    if args.ua is not None:
        ua = args.ua
    else:
        if args.vary:
            possibles = [
                ua,
                'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) ' \
                + 'AppleWebKit/525.19 (KHTML, like Gecko) ' \
                + 'Chrome/1.0.154.53 Safari/525.19',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) ' \
                + 'AppleWebKit/537.36 (KHTML, like Gecko) ' \
                + 'Chrome/40.0.2214.38 Safari/537.36',
                'Mozilla/5.0 (Linux; U; Android 2.3.5; zh-cn; ' \
                + 'HTC_IncredibleS_S710e Build/GRJ90) ' \
                + 'AppleWebKit/533.1 (KHTML, like Gecko) ' \
                + 'Version/4.0 Mobile Safari/533.1'
                ]
            ua = possibles[random.randint(1,len(possibles)-1)]

    headers = [('User-Agent', ua)]

    for line in [
        ('Accept',
         'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        ),
        ('Accept-Language', 'en-gb,en;q=0.5'),
        ('Accept-Charset', 'ISO-8859-1,utf-8;q=0.7,*;q=0.7'),
        ('Keep-Alive', '115'),
        ('Connection', 'keep-alive'),
        ('Cache-Control', 'max-age=0'),
        ]:
        headers.append(line)

    b.addheaders = headers

    if args.verbose:
        b.set_debug_http(True)
        b.set_debug_redirects(True)
        b.set_debug_responses(True)

    return b

def report(args):
    stats = args.s

    bar = '============================='
    print '\n', bar
    print 'Links crawled    : {}'.format(stats.crawled_count)
    try:
        avg_time = sum(stats.times)/float(len(stats.times))
        print 'Avg load time    : {:.5f}'.format(avg_time)
    except:
        print '0',
    else:
        print '\tMax time : {:.5f}'.format(max(stats.times))
        print '\tMin time : {:.5f}'.format(min(stats.times))
        print '\tTotal    : {:.5f}'.format(sum(stats.times))
    print '\nErrors hit       : {}'.format(len(stats.err))
    if len(stats.err)>0:
        if raw_input('\tView error detail? (y/n) > ').lower()=='y':
            print '\tDisplaying top 5 errors'
            srtd_list = sorted(
                            stats.err.items(),
                            key=operator.itemgetter(1)
                            )
            for key in srtd_list[:5]:
                print '\t{}\n\t\tCount : {}'.format(key,stats.err[key])
    print bar

def count_beans(stats,s):
    s.crawled(stats['crawled'])
    s.time(stats['times'])
    for e in stats['err']:
        s.err(e)

def jobs_terminate(args,jobs):
    print 'Terminating jobs...'
    for j in jobs:
        if args.report:
            retval = j[1].recv()
            if args.debug:
                print 'Received : ', retval, '\n'
            count_beans(retval,args.s)
        j[0].terminate()

def jobs_join(args,jobs):
    for j in jobs:
        if args.report:
            count_beans(j[1].recv(),args.s)
        j[0].join(args.maxtime)

if __name__=="__main__":

    start = time.clock()
    args = parse_arguments()
    args.start = start
    args.s = Stats()
    jobs = []

    try:
        for i in range(args.procs):
            p_conn, c_conn = Pipe()
            p = Process(
                        target = Spider,
                        args = ((args,c_conn),)
                        )
            p.start()
            jobs.append((p,p_conn))
        if any([j[0].is_alive() for j in jobs]):
            time.sleep(0.1)
        else:
            jobs_join(args,jobs)
    except KeyboardInterrupt:
        print '\nKeyboard interrupt detected!'
        jobs_terminate(args,jobs)
    except Exception as e:
        jobs_terminate(args,jobs)
        if args.debug:
            raise
        else:
            print '\nError encountered :', str(e)
            jobs_terminate(args,jobs)
    else:
        print '[*] Crawl completed successfully'
    finally:
        if args.report: report(args)
