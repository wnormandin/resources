import mechanize
import urlparse
from sys import argv
import socket

surl = argv[1] if 'http' in argv[1] else 'http://'+argv[1]
urls = []
cachedDoms = {}
br = mechanize.Browser()
br.set_handle_robots(False)
br.addheaders = [('User-agent', 'Firefox')]

def dig(domain):
   if domain in cachedDoms: return cachedDoms[domain]
   cachedDoms[domain]=address=socket.gethostbyname(domain)
   return address

ip = dig(urlparse.urlparse(surl).hostname)

def getLinks(url):
   print "Scraping: "+url
   url = 'http://'+url if 'http' not in url else url
   resp = br.open(url)
   for link in br.links():
      if link.absolute_url not in urls:
         dom = urlparse.urlparse(link.absolute_url).hostname
         if dom and  ip == dig(dom):
            urls.append(link.absolute_url)
            try:
               getLinks(link.absolute_url)
            except:
               print "ERROR: skipping "+url

getLinks(surl)
