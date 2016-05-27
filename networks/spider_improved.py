#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import mechanize
import urlparse
import random
import signal
import socket
import time
import multiprocessing
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

    def time(self,time):
        # add time to the list for averaging
        self.times.append(time)

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
    def wrapper(args,kwargs):

        instance = cls(args,kwargs)
        return instance.retval

    return wrapper

@return_init
class Spider:

    """ Spider superclass, contains all essential methods """

    def __init__(self,args,stats):
        # Takes any argument-containing namespace
        if args.debug:
            print "Spider {} spawned".format(os.getpid())
        self.args = args
        self.cached_ips = {}
        self.history = []
        self.browser = prep_browser(args)
        self.url = self.prep_url(args.url)
        self.ip = self.dig(urlparse.urlparse(self.url).hostname)
        self.stats = stats

        # Grab the current worker name
        self.name = '{} ({})'.format(
                    multiprocessing.current_process().name,
                    os.getpid()
                    )

        # Start the crawl
        self.stats['crawled'] += self.get_links(self.url)
        self.retval=self.stats
        count_beans(self.stats, args.s)

    def prep_url(self,url):
        return 'http://'+url if 'http' not in url else url

    def dig(self,dom):
        if dom in self.cached_ips: return self.cached_ips[dom]
        self.cached_ips[dom] = ip = socket.gethostbyname(dom)
        return ip

    def get_links(self, url):
        if time.clock()-self.args.start >= self.args.maxtime:
            print time.clock()-self.args.start
            print self.args.maxtime
            return 0
        print '{} : Crawling '.format(self.name), url
        start = time.clock()
        req = self.browser.open(url)
        cnt = 1
        self.stats['time']=time.clock()-start
        for link in self.browser.links():
            if link.absolute_url not in self.history:
                ln = link.absolute_url
                dom = urlparse.urlparse(ln).hostname
                if dom and self.ip == self.dig(dom):
                    self.history.append(ln)
                    try:
                        cnt += self.get_links(ln)
                    except Exception as e:
                        if self.args.debug:
                            print '{} : '.format(ln),str(e)
                        self.stats['err'].append(
                            { 'error': str(e),'url':ln }
                            )
        return cnt

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
            ua = possibles[random.randint(1,len(possibles))]

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

def report(stats,start):

    bar = '============================='
    print bar
    print 'Links crawled : ', stats.crawled_count
    try:
        print 'Average time  : ', sum(stats.times)/float(len(stats.times))
    except:
        print '0',
    else:
        print '\n\tMax time : ', max(stats.times)
        print '\tMin time : ', min(stats.times)
    print '\nErrors hit    : ', len(stats.err)
    if len(stats.err)>0:
        if raw_input('\tView error detail? (y/n) > ').lower()=='y':
            print '\tDisplaying top 5 errors'
            srtd_list = sorted(stats.err.items(),key=operator.itemgetter(1))
            for key in srtd_list[:5]:
                print '\t{}\n\t\tCount : {}'.format(key,stats.err[key])
    print '\nTook {}s'.format(time.clock()-start)
    print bar

def count_beans(stats,s):
    s.crawled(stats['crawled'])
    s.time(stats['time'])
    for e in stats['err']:
        s.err(e)

def jobs_terminate(jobs):
    for j in jobs:
        j.close()

def jobs_join(jobs):
    for j in jobs:
        j.join()

if __name__=="__main__":

    start = time.clock()
    args = parse_arguments()
    args.start = start
    args.s = Stats()
    jobs = []
    with multiprocessing.Manager() as manager:
        stats = manager.dict()
        stats['err']=[]
        stats['crawled']=0

        # multiprocessing.pool/apply async
        # Block signals before creating the process pool
        #orig_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
        #pool = multiprocessing.Pool()
        # return to original handler
        #signal.signal(signal.SIGINT, orig_sigint_handler)

        try:
            for i in range(args.procs):
                #r = pool.apply_async(Spider, (args,), callback=count_beans)
                #r.wait()
                p = multiprocessing.Process(
                            target = Spider,
                            args = (args,stats)
                            )
                p.start()
                jobs.append(p)
        except KeyboardInterrupt:
            print 'Keyboard interrupt detected!'
            jobs_terminate(jobs)
        except Exception as e:
            jobs_terminate(jobs)
            if args.debug:
                raise
            else:
                print 'Error encountered :', str(e)
        else:
            print '[*] Crawl completed'
            #pool.close()
            #pool.join()
            jobs_join(jobs)
        finally:
            if args.report: report(args.s, start)
