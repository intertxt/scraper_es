from bs4 import BeautifulSoup
import os
import argparse
import xml.etree.ElementTree as ET
import json
import re
import html



parser = argparse.ArgumentParser(description='generate clean XML-files from HTML-files')
parser.add_argument('-p','--path_to_data',type=str,help="directory where all the different data is stored")
parser.add_argument('-d','--directory',type=str,default='BL_Gerichte_clean',help='current directory for the scraper')
parser.add_argument('-t','--type',type=str, default=".xml", help="default filetype (html or pdf usually)")

args = parser.parse_args()

PATH_TO_DATA = args.path_to_data

def iterate_files(directory, filetype):
    counter = 0
    filename_list = []
    for filename in sorted(os.listdir(directory)):
        if filename.endswith(filetype):
            fname = os.path.join(directory, filename)
            with open(fname, 'r', encoding='utf-8') as file:
                if '  ' in file.read():
                    tree = ET.parse(os.path.join(directory, filename))
                    counter += 1
                    print(filename[:-4])
                    filename_list.append(filename[:-4])
                    print('\n')
                    # ET.dump(tree)
                    print('\n')
    print(counter)
    print(filename_list)
                # tree = ET.parse(os.path.join(directory, filename))
                # root = tree.getroot()
                # print(filename[:-4])
                # print('\n')
                # for pm in root.findall(".//p[@type='paragraph_mark']"):
                #     print(pm.text)
                # print('\n')




def main():

    iterate_files(PATH_TO_DATA+args.directory, args.type)

if __name__ == '__main__':
	main()