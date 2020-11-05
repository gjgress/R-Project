import pandas as pd
import sqlite3
import urllib.parse
import requests
import re
import lxml
import time
from anglicize import anglicize
from bs4 import BeautifulSoup
from selenium import webdriver

conn = sqlite3.connect('../arXivMetadata.sqlite')

authors = conn.execute("SELECT AuthorsParsed from arXiv")
titles = conn.execute("SELECT Title from arXiv")
doi = conn.execute("SELECT DOI from arXiv")
schools = conn.execute("SELECT NAME from ColUni")


# Converts arXiv titles into HTML-parseable titles, for querying
htmltitles = list(map(urllib.parse.quote,list(zip(*titles.fetchall()))[0] ))
htmlauthors = list(zip(*authors.fetchall()))[0]

authuni = []

classid = "nova-v-person-inline-item"

most_common_user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36",
]

def request_with_proxy(url):
    
    #replace with your mobile proxy provider URL 
    proxy = ""
    payload = {
        "proxies": {"http": proxy, "https": proxy},
        "url": url,
        "verify": False,
        "timeout": 60,
        "headers": {
            "User-Agent": random.choice(most_common_user_agents),
            "referrer": "https://www.google.com",
        },
    }
    
    try:
        start = time.time()
        resolved_url = ''
        response = requests.get(**payload)
        status_code = response.status_code
        resolved_url = response.url
        if 200 <= status_code <= 299 or status_code == 404:
            body = response.text
            #print(body)
        else:
            body = f"Server responded with {status_code}"
    except Exception as e:
        body, status_code = str(e), 500
        print("-------")
        print(time.time() - start, proxy, body, e)
        print("-------")
        return {"statusCode": 500, "body": body, "time": time.time() - start, "resolved_url": resolved_url}
    finally:
        return {"statusCode": status_code, "body": body, "time": time.time() - start,  "resolved_url": resolved_url}


def send_request(url):
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
    return(response)

for i,title in enumerate(htmltitles):
    authorslist = eval("list(" + htmlauthors[i] + ")")
    time.sleep(1/250)
    r = send_request('https://www.researchgate.net/search/publication?q=' + title)
    soup = BeautifulSoup(r.text,'lxml')
    for author in authorslist:
        if authuni.count(author)==0:
            r2 = send_request('https://www.researchgate.net/' + soup.find("a", {'href': re.compile(re.sub("[^0-9a-zA-Z]","",anglicize(author[0])),flags=re.I)}).attrs['href'])
            soup2 = BeautifulSoup(r2.text, 'lxml')
            if r2.url.find("profile")>=0:
                university = soup2.find("div", class_="nova-e-text nova-e-text--size-m nova-e-text--family-sans-serif nova-e-text--spacing-none nova-e-text--color-grey-600").contents[0].contents[0].contents[0]
            else:
                university = BeautifulSoup(str(list(soup2.find("h1", class_="nova-e-text nova-e-text--size-xl nova-e-text--family-sans-serif nova-e-text--spacing-none nova-e-text--color-grey-600 sci-con__header-title").children)[2]),"lxml").text
            authuni.append([author,university])
dfauthuni = pd.DataFrame(authuni)
dfauthuni.to_csv("authorsuni.csv")
