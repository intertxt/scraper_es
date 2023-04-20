#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Getting the most important statistics for each new raw file.


# Use this command in your shell:
# python3.8 get_stats_raw.py [-args]

# start of last crawl was 2023-04-05 (YYYY-MM-DD)


# Import necessary modules.
import xml.etree.ElementTree as ET
import os
import argparse
import pandas as pd
from typing import List
import datetime
import warnings

parser = argparse.ArgumentParser(description="get stats on newly crawled files")
parser.add_argument("-p", "--path_to_data", type=str, help="directory that contains folders")
parser.add_argument("-pf", "--path_to_files", type=str, help="directory that contains files directly")
parser.add_argument("-dd", "--crawl_date", type=str,
                    help="only files that were crawled from this date onwards are considered. use the following format: YYYY-MM-DD")
parser.add_argument("-out", "--output_format", type=str, help="choose output format between 'csv' and 'pickle'")

args = parser.parse_args()


def get_date(file):
    file_date = file.strip(".pdfhtml").split("_")[-1]
    if len(file_date.split("-")) == 3 and len(file_date.split("-")[0]) == 4 and not file_date == "nodate":
        date_nr = file_date.split("-")
        e_date = datetime.date(int(date_nr[0]), int(date_nr[1]), int(date_nr[2]))
    elif len(file_date.split("-")) == 3 and len(file_date.split("-")[0]) != 4 and not file_date == "nodate":
        date_nr = file_date.split("-")
        e_date = datetime.date(int(date_nr[2]), int(date_nr[1]), int(date_nr[0]))
    else:
        e_date = "0000-00-00"
    return e_date


def main():
    d = {"folder": [],
         "filename": [],
         "crawl_date": [],
         "entscheid_date": [],
         "canton": [],
         "size": [],
         "datatype": []}

    crawl_date_list = [int(_) for _ in args.crawl_date.split("-")] if args.crawl_date else [1900, 1, 1]
    crawl_date = datetime.date(crawl_date_list[0], crawl_date_list[1], crawl_date_list[2])
    os.chdir("/")

    if args.path_to_files:
        folder = args.path_to_files
        print(f"Current folder:\t{folder}")
        for file in sorted(os.listdir(folder))[:20]:
            stat = os.stat(os.path.join(folder, file))
            time_stamp = stat.st_ctime
            date = datetime.date.fromtimestamp(time_stamp)
            if date >= crawl_date:
                if not file.endswith("json"):
                    datatype = file.split(".")[1]  # usually either pdf or html
                    e_date = get_date(file)
                    level = "CH" if file.startswith("CH") else file.split("_")[0]
                    size = stat.st_size
                    d["folder"].append(folder.split("/")[-1])
                    d["filename"].append(file)
                    d["crawl_date"].append(date)
                    d["entscheid_date"].append(e_date)
                    d["canton"].append(level)
                    d["size"].append(size)
                    d["datatype"].append(datatype)

    elif args.path_to_data:
        for folder in os.listdir(args.path_to_data):
            folder = os.path.join(args.path_to_data, folder)
            print(f"Current folder:\t{folder}")
            for file in sorted(os.listdir(folder))[:20]:
                stat = os.stat(os.path.join(folder, file))
                time_stamp = stat.st_ctime
                date = datetime.date.fromtimestamp(time_stamp)
                if date >= crawl_date:
                    if not file.endswith("json"):
                        datatype = file.split(".")[1]  # usually either pdf or html
                        e_date = get_date(file)
                        level = "CH" if file.startswith("CH") else file.split("_")[0]
                        size = stat.st_size
                        d["folder"].append(folder.split("/")[-1])
                        d["filename"].append(file)
                        d["crawl_date"].append(date)
                        d["entscheid_date"].append(e_date)
                        d["canton"].append(level)
                        d["size"].append(size)
                        d["datatype"].append(datatype)


    else:
        raise Warning("Please enter a path to a folder.")

    df = pd.DataFrame.from_dict(d)

    today = datetime.date.today()

    if args.output_format == "csv":  # for csv
        with open(f"/usr/local/zhaw/app/sur/scraper_kantone/stats/data/{today}_new_raw_stats.pickle", "w", encoding="utf-8") as f:
            df.to_csv(f, index=False)

    elif args.output_format == "pickle":  # for pickle
        df.to_pickle(f"/usr/local/zhaw/app/sur/scraper_kantone/stats/data/{today}_new_raw_stats.pickle")

    else:
        raise Warning("Please enter an output format.")


if __name__ == "__main__":
    main()
