import pandas as pd
import sqlite3
import urllib.parse
import requests
import re
import lxml
from lxml.html import fromstring
import time
import random
import csv
#import asyncio
#from proxybroker import Broker
from anglicize import anglicize
from bs4 import BeautifulSoup
from selenium import webdriver

conn = sqlite3.connect('../arXivMetadata.sqlite')

authors = conn.execute("SELECT AuthorsParsed from arXiv")
titles = conn.execute("SELECT Title from arXiv")
doi = conn.execute("SELECT DOI from arXiv")
schools = conn.execute("SELECT NAME from ColUni")

with open('authorsuni.csv', newline='') as f:
    reader = csv.reader(f)
    authuni = list(reader)

# Converts arXiv titles into HTML-parseable titles, for querying
htmltitles = list(map(urllib.parse.quote,list(zip(*titles.fetchall()))[0] ))
htmlauthors = list(zip(*authors.fetchall()))[0]

## Common agents that should be used alongside proxies

most_common_user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36",
]


## ProxyBroker method-- works, but proxies don't seem effective

#async def show(proxies):
#    while True:
#        proxy = await proxies.get()
#        if proxy is None: break
#        return proxy.host
#
#proxies = asyncio.Queue()
#broker = Broker(proxies)
#tasks = asyncio.gather(
#    broker.find(types=['HTTP', 'HTTPS'], limit=1),
#    show(proxies))

#loop = asyncio.get_event_loop()
#loop.run_until_complete(tasks)


## Generalized send_request, specify which proxy system to use
def send_request(url,counter,author, scraper):

    if(counter>5):
        raise Exception("ResearchGate blocking incoming proxies, cannot scrape data, failed on URL \n" + url)

    if(scraper=="scrapingbee"):
        response = scrapingbee(url,js="false")
    elif(scraper=="free"):
        response = free_proxy(url)
    elif(scraper=="crawlera"):
        response = crawlera(url)
    else:
        raise Exception("No suitable proxy method given")

    print('Response HTTP Status Code: ', response.status_code)
    print('Response HTTP Response Body: ', response.content)
    
    while (response.text.find("Please, wait while we are validating your browser") != -1):
        counter += 1
        send_request(url,counter,author,scraper)

    print(response.text)

    # This isn't perfect. At the moment, if it doesn't find the name it ought to find, it assumes the proxy blocks it. Ideally this should be rewritten to recognize if the proxy is getting blocked, or if there are no available proxies, and count different counters. If for some OTHER reason (i.e. the page loads but the author just isn't there) it cannot find the author, THEN it should just allow it through, so that the author will be paired with university = "". Caution must be used otherwise it will fill a bunch of entries with blank entries when the proxy fails... This is a task to resolve another time
    if(BeautifulSoup(response.text,'lxml').find("a", {'href': re.compile(re.sub(" ", "-",re.sub("[^0-9a-zA-Z\- ]","",anglicize(author))),flags=re.I)})== None):
        counter += 1
        send_request(url,counter,author,scraper)
    return(response)


def free_proxy(url):
    try:
        proxylist
    except NameError:
        proxylist = []
    if(len(proxylist)==0):
        proxylist = get_proxies()
    proxy = random.choice(proxylist)
    proxylist.remove(proxy)
    proxies = {
            "http": proxy,
            "https": proxy,
            }
    return(requests.get(url=url, proxies=proxies))

def get_proxies():
    url = 'https://free-proxy-list.net/'
    response = requests.get(url)
    parser = fromstring(response.text)
    proxies = re.findall("^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?).*",response.text,re.MULTILINE)
    return(proxies)

## Uses scrapingbee api-- but costs money for >1000 requests
def scrapingbee(url, js):
    return(requests.get(url=url,
        params={
            "api_key": "PVOYIDL5FRF939XKB13NVDML045BDNRXG9910JNQWEFGNJS61PGGPPPXP72CJSZ4KNPA0F4VPQWNZHHH",
            "url": url,
            "render_js": js
        }

    ))


def crawlera(url):

    # Counter so I don't accidentally overuse the allotted amount and charge myself money...
    counter = int(retrieve_count())
    if(counter>9500):
        raise Exception("Too close to usage cap-- change proxies or manually change cap")

    proxy_host = "proxy.crawlera.com"
    proxy_port = "8010"
    proxy_auth = "c47caddc62f54928b5d825cd0f331e78:" # Make sure to include ':' at the end
    proxies = {"https": "https://{}@{}:{}/".format(proxy_auth, proxy_host, proxy_port),
          "http": "http://{}@{}:{}/".format(proxy_auth, proxy_host, proxy_port)}
    counter = counter+1
    r = requests.get(url,proxies=proxies,verify=False)

    update_count(str(counter))

    return(r)

def update_count(count):
    with open("UsageCount","w") as f:
        f.write(count)

def retrieve_count():
    with open("UsageCount","r") as f:
        return(f.readline().strip())

# Returns list of proxies from freeproxylist. Unfortunately, requires a proxy... WIP

#def get_proxy_from_freeproxylist():
#    proxies = ''
#    counter = 1
#    has_next_page = True
#    r = requests.get('http://freeproxylists.net/?c=&pt=&pr=HTTPS&a%5B%5D=2&u=0')
#    counter += 1
#
#    soup = BeautifulSoup(r.content, 'html.parser')
#    print(soup)
#    lines = soup.select('table.DataGrid tbody tr')
#    for i in lines[1:]: 
#        
#        if not 'adsbygoogle' in i.text:
#            proxy = i.select('td a')[0].text
#            port = i.select('td')[1].text
#            proxies += proxy + ':' + port + '\n'
#    return(proxies)

## Generalized proxy request-- WIP

#def request_proxy(url):
#    #random_proxy = random.choice(proxylist)
#    # random_proxy = "62.210.75.50:13732"
#    payload = {
#            "proxies": {"http": loop.run_until_complete(tasks)},
#        "url": url,
#        "verify": True,
#        "timeout": 60,
#        "headers": {
#            "User-Agent": random.choice(most_common_user_agents),
#            "referrer": "https://www.google.com",
#    }}
#    return(requests.get(**payload))


## This section is where the scraping happens

lastchecked = int(authuni[-1][0])
for j, title in enumerate(htmltitles[lastchecked+1]):
    i = j+lastchecked+1
    # turn database into python list
    authorslist = eval("list(" + htmlauthors[i] + ")")
    title = htmltitles[i]
    # pull publications and soupify
    time.sleep(1/250)

    # Prevents edge cases where organizations are listed as authors...
    if (("The " in authorslist[0][0]) !=True):
        r = send_request('https://www.researchgate.net/search/publication?q=' + title,0,authorslist[0][0],scraper="crawlera")
        if (r == ""):
            for author in authorslist:
                university = ""
                authuni.append([author,university])
                with open('authorsuni.csv', 'a+', newline='') as f:
                    csv_writer = csv.writer(f)
                    csv_writer.writerow([i,author,university])
        else:
            soup = BeautifulSoup(r.text,'lxml')

            for author in authorslist:
                authorcount = 0
                for lists in authuni:
                    authorcount += lists.count(author)
                if (authorcount==0 & ("The " in author[0])):
                    print(author)
                    print(r.url)
                    r2 = send_request('https://www.researchgate.net/' + soup.find("a", {'href': re.compile(re.sub(" ", "-",re.sub("[^0-9a-zA-Z\- ]","",anglicize(author[0]))),flags=re.I)}).attrs['href'],0,author[0],scraper="crawlera")
                    soup2 = BeautifulSoup(r2.text, 'lxml')
                    if r2.url.find("profile")>=0:
                        university = soup2.find("div", class_="nova-e-text nova-e-text--size-m nova-e-text--family-sans-serif nova-e-text--spacing-none nova-e-text--color-grey-600").contents[0].contents[0].contents[0]
                    else:
                        if (hasattr(soup2.find("h1", class_="nova-e-text nova-e-text--size-xl nova-e-text--family-sans-serif nova-e-text--spacing-none nova-e-text--color-grey-600 sci-con__header-title"),'children')==False):
                            university = ""
                        elif (len(list(soup2.find("h1", class_="nova-e-text nova-e-text--size-xl nova-e-text--family-sans-serif nova-e-text--spacing-none nova-e-text--color-grey-600 sci-con__header-title").children)
    )>=3 | (soup2.title!=("<title>17+ million researchers on ResearchGate</title>"))):
                            university = BeautifulSoup(str(list(soup2.find("h1", class_="nova-e-text nova-e-text--size-xl nova-e-text--family-sans-serif nova-e-text--spacing-none nova-e-text--color-grey-600 sci-con__header-title").children)[2]),"lxml").text
                        else:
                            university = ""
                    authuni.append([author,university])
                    with open('authorsuni.csv', 'a+', newline='') as f:
                        csv_writer = csv.writer(f)
                        csv_writer.writerow([i,author,university])

#dfauthuni = pd.DataFrame(authuni)
#dfauthuni.to_csv("authorsuni.csv")
