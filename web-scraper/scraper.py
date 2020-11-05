import pandas as pd
import sqlite3
import urllib.parse
import requests
import re
import lxml
import time
import random
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

authuni = []

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


## Uses scrapingbee api-- but costs money for >1000 requests

def send_request(url,counter):

    if(counter>5):
        raise Exception("ResearchGate blocking incoming proxies, cannot scrape data")

    response = requests.get(
        url="https://app.scrapingbee.com/api/v1/",
        params={
            "api_key": "PVOYIDL5FRF939XKB13NVDML045BDNRXG9910JNQWEFGNJS61PGGPPPXP72CJSZ4KNPA0F4VPQWNZHHH",
            "url": url,
            "render_js": "false"
        },

    )
    print('Response HTTP Status Code: ', response.status_code)
    print('Response HTTP Response Body: ', response.content)
    
    while (BeautifulSoup(response.text,'lxml').find("a", {'href': re.compile(re.sub("[^0-9a-zA-Z]","",anglicize(authorslist[0][0])), flags=re.I)})== None):
        counter += 1
        send_request(url,counter)
    return(response)

## Returns list of proxies from freeproxylist. Unfortunately, requires a proxy... WIP

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

for i,title in enumerate(htmltitles[0:400]):
    # turn database into python list
    authorslist = eval("list(" + htmlauthors[i] + ")")

    # pull publications and soupify
    time.sleep(1/250)
    r = send_request('https://www.researchgate.net/search/publication?q=' + title,0)
    soup = BeautifulSoup(r.text,'lxml')


    for author in authorslist:
        if authuni.count(author)==0:
            r2 = send_request('https://www.researchgate.net/' + soup.find("a", {'href': re.compile(re.sub("[^0-9a-zA-Z]","",anglicize(author[0])),flags=re.I)}).attrs['href'],0)
            soup2 = BeautifulSoup(r2.text, 'lxml')
            if r2.url.find("profile")>=0:
                university = soup2.find("div", class_="nova-e-text nova-e-text--size-m nova-e-text--family-sans-serif nova-e-text--spacing-none nova-e-text--color-grey-600").contents[0].contents[0].contents[0]
            else:
                university = BeautifulSoup(str(list(soup2.find("h1", class_="nova-e-text nova-e-text--size-xl nova-e-text--family-sans-serif nova-e-text--spacing-none nova-e-text--color-grey-600 sci-con__header-title").children)[2]),"lxml").text
            authuni.append([author,university])
dfauthuni = pd.DataFrame(authuni)
dfauthuni.to_csv("authorsuni.csv")
