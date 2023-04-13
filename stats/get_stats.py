#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Getting the most important statistics for each file.
# Use this command in your shell:
# python3.10 get_stats.py


# Import necessary modules.
import xml.etree.ElementTree as ET
import os
import argparse
import pandas as pd
from typing import List
import datetime

parser = argparse.ArgumentParser(description="extract the earliest and lates filedate out of folder")
# parser.add_argument("-p", "--path_to_data", type=str, help="directory that contains clean files")

args = parser.parse_args()

def get_date():
    pass

def get_courtname():
    pass

def get_canton():
    pass

def get_foldername():
    pass

def get_source_format():
    pass

def get_filename():
    pass

def get_sample(n, seed=None):
    """
    get random sample of n files.
    add a seed to ensure reproducibility.
    """
    pass

def format_date(date_string: str) -> List[int]:
    """"Get the date string into a suitable format for datetime and creat a date object."""
    date_list = date_string.split("-") if "-" in date_string else date_string.split(".")
    if len(date_list[2]) != 2 and len(date_list[2]) != 4:
        print(f"This date resulted in an issue during formatting: {date_string}")
        return datetime.date(2011, 1, 1)
    if len(date_list[0]) == 4:
        date_list =  [int(elem) for elem in date_list]
    else:
        date_list = [int(elem) for elem in date_list[::-1]]
    if date_list != [0, 0, 0]:
        # print(date_list)
        return datetime.date(date_list[0], date_list[1], date_list[2]) # date object with yyyy, mm, dd


def main():
    directory = args.path_to_data
    directory_dates = []
    for file in sorted(os.listdir(directory)):
        tree = ET.parse(directory+"/"+file)
        root = tree.getroot()
        # print(file)
        if format_date(root.attrib["date"]): directory_dates.append(format_date(root.attrib["date"]))
    print(directory.split("/")[2])
    print(f"earliest date: {min(directory_dates)}")
    print(f"latest date: {max(directory_dates)}\n")


if __name__ == "__main__":
    main()