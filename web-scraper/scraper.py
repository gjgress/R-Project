import pandas as pd
import sqlite3
import urllib.parse
import requests
import re
import lxml
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

for i,title in enumerate(htmltitles[0:1]):
    authorslist = eval("list(" + htmlauthors[i] + ")")
    r = requests.get('https://www.researchgate.net/search/publication?q=' + title)
    soup = BeautifulSoup(r.text,'lxml')
    for author in authorslist:
        if authuni.count(author)==0:
            print(soup)
            r2 = requests.get('https://www.researchgate.net/' + soup.find("a", {'href': re.compile(re.sub("[^0-9a-zA-Z]","",anglicize(author[0])),flags=re.I)}).attrs['href'])
            soup2 = BeautifulSoup(r2.text, 'lxml')
            if r2.url.find("profile")>=0:
                university = soup2.find("div", class_="nova-e-text nova-e-text--size-m nova-e-text--family-sans-serif nova-e-text--spacing-none nova-e-text--color-grey-600").contents[0].contents[0].contents[0]
            else:
                university = soup2.find("h1", class_="nova-e-text nova-e-text--size-xl nova-e-text--family-sans-serif nova-e-text--spacing-none nova-e-text--color-grey-600 sci-con__header-title").contents[1].contents[0].contents[0]
            authuni.append([author,university])

dfauthuni = pd.DataFrame(authuni)
dfauthuni.to_csv("authorsuni.csv")
