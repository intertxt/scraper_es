from bs4 import BeautifulSoup
import os
import argparse
import xml.etree.ElementTree as ET
import json
import re
import html
import unicodedata
from collections import Counter


ALLOWED_CLASSES = ["MsoTableGrid"]

parser = argparse.ArgumentParser(description='generate clean XML-files from HTML-files')
parser.add_argument('-p','--path_to_data',type=str,help="directory where all the different data is stored")
parser.add_argument('-d','--directory',type=str,default='CH_BGE_clean',help='current directory for the scraper') ###
parser.add_argument('-t','--type',type=str, default=".html", help="default filetype (html or xml usually)") ###

args = parser.parse_args()

PATH_TO_DATA = args.path_to_data

def get_files_wo_pendant(directory):
    freq_dict = {}
    for filename in sorted(os.listdir(directory)):
        if filename[:-5] not in freq_dict:
            freq_dict[filename[:-5]] = 1
        else:
            freq_dict[filename[:-5]] += 1
    missing_jsons = [k for k, v in freq_dict.items() if v == 1]
    return missing_jsons


def get_files_wo_pmark(directory):
    counter = 0
    filename_list = []
    for filename in sorted(os.listdir(directory)):
        fname = os.path.join(directory, filename)
        with open(fname, 'r', encoding='utf-8') as file:
            if '<p type="paragraph_mark">' not in file.read():
                counter += 1
                filename_list.append(filename[:-4])
    # print(filename_list, counter)
    return (filename_list)


def get_files_w_tables(directory, filetype):
    counter = 0
    filename_list = []
    for filename in sorted(os.listdir(directory)):
        if filename.endswith(filetype):
            fname = os.path.join(directory, filename)
            with open(fname, 'r', encoding='utf-8') as file:
                if '<table' in file.read():
                # if re.search(r"^[1-9]\.[a-z]\)", file.read()):
                #     match = re.search(r"^[1-9]\.[a-z]\)", file.read()).group(0)
                    #tree = ET.parse(os.path.join(directory, filename))
                    counter += 1
                    #print(filename[:-4])
                    filename_list.append(filename[:-5])
                        # print('\n')
                        # # ET.dump(tree)
                        # print('\n')
    print(filename_list, counter)
                        # print(filename, match)
                    # tree = ET.parse(os.path.join(directory, filename))
                    # root = tree.getroot()
                    # print(filename[:-4])
                    # print('\n')
                    # for pm in root.findall(".//p[@type='paragraph_mark']"):
                    #     print(pm.text)
                    # print('\n')
    return(filename_list)


def get_missing_files(directory, filetype):
    counter = 0
    dir_pre = set()
    for filename in sorted(os.listdir(directory)):
        dir_pre.add(filename[:-5]+".xml")
    dir_post = set(sorted(os.listdir("/home/admin1/tb_tool/clean_scraper_data/VD_FindInfo_clean")))
    missing_files = dir_pre-dir_post
    missing_files = list(missing_files)
    list_of_missing_filenames = []
    for filename in missing_files:
        filename = filename[:-4]+".html"
        list_of_missing_filenames.append(filename)
    return list_of_missing_filenames


def get_files_wo_text(directory, filetype):
    counter = 0
    filename_list = []
    for filename in sorted(os.listdir(directory)):
        if filename.endswith(filetype):
            fname = os.path.join(directory, filename)
            with open(fname, 'r', encoding='utf-8') as file:
                parsed_html = BeautifulSoup(file.read(), "html.parser")  # read html
                text = []
                tag_list = parsed_html.findAll(["p", "table"])
                for i, tag in enumerate(tag_list):
                    if tag.name == "table":
                        # check = any(item in tag["class"] for item in ALLOWED_CLASSES)
                        if tag.has_attr("class"):
                            if any(item in tag["class"] for item in ALLOWED_CLASSES):
                                text.append(str(tag))
                                tag.decompose()
                    else:
                        # it already strips the text snippet of whitespace characters
                        tag_text = unicodedata.normalize('NFKD', tag.get_text(strip=True)).replace("\n", " ").replace(
                            "  ",
                            " ").replace(
                            "   ", " ").replace("     ", " ")
                        if tag_text == "" or tag_text == " ":
                            continue
                        else:
                            tag_text = tag_text.replace("  ", " ").replace("   ", " ").replace("     ", " ")
                            text.append(tag_text.replace("  ", " ").replace("   ", " ").replace("     ", " "))
                if not text:
                    counter += 1
                    filename_list.append(filename[:-5])
                    print(counter, filename[:-5])
                    continue
    return counter, filename


def get_missing_date_files(directory):
    for filename in sorted(os.listdir(directory)):
        if "0000" in filename:
            tree = ET.parse(filename)
            root = tree.getroot()
            return root.attrib

def main():
    # pass
    # print(get_files_wo_pendant("/home/admin1/tb_tool/scraping_data/ZH_Verwaltungsgericht"))
    # get_files_wo_pmark(PATH_TO_DATA+args.directory)
    # get_files_w_tables(PATH_TO_DATA+args.directory, args.type)
    # print(get_missing_files(PATH_TO_DATA+args.directory, args.type))
    # print(get_files_wo_text(PATH_TO_DATA+args.directory, args.type))
    print(get_missing_date_files(PATH_TO_DATA+args.directory))


if __name__ == '__main__':
	main()