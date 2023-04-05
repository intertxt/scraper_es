#!/usr/bin/env python
# coding: utf-8


# use with the following command:
# python3 crawling.py 

import requests
import urllib.request
import time
from bs4 import BeautifulSoup
import os
import argparse

url = 'https://entscheidsuche.ch/docs/'

response = requests.get(url)

print(response)  ## 200 is good -> macht pause damit der server den scraper nicht blockiert

counter = {}

def parse_arguments():
    """
    Argument Parser implementation.
    """
    parser = argparse.ArgumentParser(description="Crawl files from entscheidsuche.ch.")
    parser.add_argument("path", help="Add a path to the directory that contains the directories for all cantonal documents." )
    return parser



def isDirectory(url):
    # checkt ob es noch ein subdirectory hat / ein directory ist 
    if url.endswith("/"):
        return True
    else:
        return False


def findLinks(url, path):
    os.chdir("/")
    if not os.path.exists(path):
        print(f"This path seems to be wrong.")
        quit()
    page = requests.get(url).content
    bsObj = BeautifulSoup(page, "html.parser")
    potential_dirs = bsObj.findAll("a", href=True)  # findet alle links in der aufgerufenen seite
    for link in potential_dirs:
        if isDirectory(link["href"]):  # falls es ein directory ist wird es neu aufgerufen (rekursiv)
            if len(link["href"]) != 1 and link["href"] != "/docs/":
                newUrl = url + link["href"].lstrip("/docs")
                findLinks(newUrl, path)
        else:
            if link["href"].endswith(".json") or link["href"].endswith(".html") or link["href"].endswith(".pdf"):
                print(link["href"])
                link = link["href"].split("/")[-1]  # filename wird definiert
                directory = os.path.join(path, url.split("docs/")[-1])  # directory name wird definiert
                if not os.path.exists(directory):  # falls das directory für dieses gericht noch nicht besteht wird es erstellt
                    print("new dir:", directory)
                    os.makedirs(directory)
                    counter[directory] = 1
                else:
                    print(f"Directory {directory} already exists." )
                if not os.path.exists(directory + link):  # überprüfen, ob das file schon existiert
                    print("new_file:" + directory + link)
                    download_url = url + link
                    if directory not in counter:
                        counter[directory] = 1
                    else:
                        counter[directory] += 1
                    urllib.request.urlretrieve(download_url,
                                               directory + link)  # welcher url heruntergeladen wird + wo das file gespeichert wird
                    time.sleep(2)  # pause
                else:
                    print(f"File {directory + link} already exists." )
                    continue  # falls das file schon existiert


def main():
    args = parse_arguments().parse_args()
    findLinks(url, args.path)
    print(counter)  # analyse wie viele files gefunden wurden pro directory


if __name__ == '__main__':
    main()










