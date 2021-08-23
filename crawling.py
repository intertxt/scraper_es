#!/usr/bin/env python
# coding: utf-8


import requests
import urllib.request
import time
from bs4 import BeautifulSoup
import os


url = 'https://entscheidsuche.ch/docs/'


response = requests.get(url)

print(response) ## 200 is good -> macht pause damit der server den scraper nicht blockiert 

counter = {}


def isDirectory(url):
    # checkt ob es noch ein subdirectory hat / ein directory ist 
    if url.endswith("/"):
        return True
    else:
        return False

def findLinks(url):
    page = requests.get(url).content
    bsObj = BeautifulSoup(page, "html.parser")
    potential_dirs = bsObj.findAll("a",href=True) #findet alle links in der aufgerufenen seite 
    for link in potential_dirs:
        if isDirectory(link["href"]): #falls es ein directory ist wird es neu aufgerufen (rekursiv)
            if len(link["href"]) != 1 and link["href"] != "/docs/":
                newUrl = url + link["href"].lstrip("/docs")
                findLinks(newUrl)
        else:
            if link["href"].endswith(".json") or link["href"].endswith(".html") or link["href"].endswith(".pdf"): 
                link = link["href"].split("/")[-1]  # filenname wird definiert
                directory = url.split("docs/")[-1] # directory name wird definiert 
                if not os.path.exists(directory): # falls das directory für dieses gericht noch nicht besteht wird es erstellt
                    print("new dir:",directory)
                    os.makedirs(directory)
                    counter[directory] = 1
                download_url = url + link
                counter[directory] += 1
                urllib.request.urlretrieve(download_url, directory+link) # welcher url heruntergeladen wird + wo das file gespeichert wird
                time.sleep(2) # pause 


 

def main():
   
    findLinks(url)                  
    print(counter) # analyse wie viele files gefunden wurden pro directory


if __name__ == '__main__':
    main()










