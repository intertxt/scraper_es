#!/usr/bin/env python3.10
# -*- coding: utf-8 -*-
# Getting a sample of clean files.
# Use this command in your shell:
# python3.10 sample_generator.py


# Import necessary modules.
import os
import argparse
import sys
import random
import shutil
from pathlib import Path

# specify path to data
DIR = "../../clean_scraper_data/"

# Define argument parser
def get_argumentparser():
    parser = argparse.ArgumentParser(description="extract the earliest and lates filedate out of folder")
    parser.add_argument("--n", type=int, default=1, help="number of samples picked from each directory")
    parser.add_argument("--out_path", "-op", type=str, default="sample/", help="directory, where samples should located")
    parser.add_argument("-dirs", type=list[str], required=False, help="if set, only the listed directories will be considered")
    return parser

def get_sample(subdir, n):
    """
    Produce n sized sample.
    """
    filenames = os.listdir(os.path.join(DIR,subdir))
    filepaths = [os.path.join(DIR, subdir, f) for f in filenames]
    if len(filenames) >= n:
        sample = []
        for _ in range(n):
            sample.append(filepaths.pop(random.randrange(len(filepaths))))
        return sample
    else:
        raise Error("n is larger than the number of files in the directory. Please choose a lower number.")


def fill_dir(sample, out_dir):
    """
    Copy and move sample files from source to target directory.
    """
    for file in sample:
        shutil.copy2(file, out_dir)


def main():
    
    # get argument parser and arguments
    parser = get_argumentparser()
    args = parser.parse_args()

    # specify output path, create dir if not existing
    out_dir = args.out_path
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)

    # get samples and move them into output directory
    for subdir in sorted(os.listdir(DIR)):
        if args.dirs:
            for dir in args.dirs:
                if dir == subdir:
                    sample = get_sample(os.path.join(DIR,subdir), args.n)
                    fill_dir(sample, out_dir)
        else:
            sample = get_sample(subdir, args.n)
            fill_dir(sample, out_dir)

    # give log info
    if os.path.exists(out_dir) and os.listdir(out_dir):
        print(f"Done! Please find your sample file(s) in {out_dir}.")
    else:
        raise Warning("Sample was *not* collected!")


if __name__ == "__main__":
    main()