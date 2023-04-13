#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Script for checking if the number of paragraphs in a converted XMl makes sense,
# in order to see if the "header" was successfully separated from the main text.

# Use this command in your shell:
# python3.10 check_paragraphs.py -p /home/admin1/tb_tool/clean_scraper_data/folder_to_be_checked


# Import necessary modules.
import xml.etree.ElementTree as ET
import os
import argparse
from typing import List
import datetime

parser = argparse.ArgumentParser(description="extract the earliest and lates filedate out of folder")
parser.add_argument("-p", "--path_to_data", type=str, help="directory that contains clean files")

args = parser.parse_args()


def main():
    file_counter = 0
    directory = args.path_to_data
    file_list = []
    for file in sorted(os.listdir(directory)):
        tree = ET.parse(directory+"/"+file)
        root = tree.getroot()
        counter = 0
        # for p in root[0].findall("p"):
        #     counter += 1
        # if counter > 100:
        #     file_counter += 1
        #     print(file)
        for p in root[0].findall("p"):
            if p.attrib == {'type': 'paragraph_mark'}:
                counter += 1
                break
        if counter == 0:
            file_counter += 1
            file_list.append(file[:-4])
            # print(file)
        else:
            continue
    print(file_counter)
    print(file_list)

if __name__ == "__main__":
    main()