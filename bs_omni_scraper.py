#!/usr/bin/env python
# coding: utf-8
# scraper for BS_Omni

from bs4 import BeautifulSoup
import os
import argparse
from typing import List
import xml.etree.ElementTree as ET
import json
import re
import unicodedata
import glob
from duplicate_checker import get_duplicates


parser = argparse.ArgumentParser(description="generate clean XML-files from HTML-files")
parser.add_argument("-p","--path_to_data",type=str,help="directory where all the different data is stored")
parser.add_argument("-d","--directory",type=str,default="BS_Omni",help="current directory for the scraper")
parser.add_argument("-t","--type",type=str, default=".html", help="default filetype (html or pdf usually)")

args = parser.parse_args()

PATH_TO_DATA = args.path_to_data

SAVE_PATH = "/home/admin1/tb_tool/clean_scraper_data/BS_Omni_clean/"

absatz_pattern = r"^(\s)?[0-9]+\.([0-9]+(\.)?)*(\s-\s[0-9]+\.([0-9]+(\.)?)*)?"
absatz_pattern2 = r"^(\s)?[0-9]+\.([0-9]+(\.)?)*(\s-\s[0-9]+\.([0-9]+(\.)?)*)?\s-\s[0-9]+\.([0-9]+(\.)?)*(\s-\s[0-9]+\.([0-9]+(\.)?)*)?"
datum_pattern = r"[0-9][0-9]?\.[\s]{1,2}([A-Z][a-z]+|März)\s[1-9][0-9]{3}"

# def check_if_duplicate(filename) -> bool:
# 	"""Check if same file with same name has already been converted.
# 	Returns True if file exists in destination directory.
# 	Returns False if file does not yet exist in destination directory."""
# 	filename = filename.rstrip("nodate.html")
# 	if glob.glob(SAVE_PATH+filename+"*") != []:
# 		return True
# 	else:
# 		return False


def parse_text(parsed_html) -> List[str]:
	"""Get text out of HTML-files."""
	text = []
	for tag in parsed_html.findAll(["p"]):
		tag_text = unicodedata.normalize("NFKD", tag.get_text()).replace("\n", " ").replace("      ", " ")
		tag_text = re.sub(r"\s\s+", " ", tag_text).strip()
		text.append(tag_text)
	filter_list = list(filter(lambda x: x != "", text))
	text = list(filter_list)
	return text


def split_absatznr(text_list) -> List[str]:
	"""Split "paragraph_mark" from rest of the text."""
	paragraph_list = []
	for i, element in enumerate(text_list):
		if element == "Fr." and re.match(absatz_pattern, text_list[i+1]):
			paragraph_list.append(element+" "+text_list[i+1])
			del text_list[i+1]
		elif element == '-':
			paragraph_list.append(element+" "+text_list[i+1])
			del text_list[i+1]
		elif re.search(absatz_pattern2, element):
			match2 = re.search(absatz_pattern2, element).group(0)
			if element.startswith(match2):
				paragraph_list.append(match2)
				paragraph_list.append(element.lstrip(match2))
			elif element == match2:
				paragraph_list.append(element)
			elif element.startswith("(...)"):
				paragraph_list.append("(...)")
				paragraph_list.append(match2)
				paragraph_list.append(element.lstrip("(...)"+match2))
			else:
				paragraph_list.append(element)
		elif re.search(absatz_pattern, element):
			match = re.search(absatz_pattern, element).group(0)
			if element.startswith(match) and i+1 < len(text_list) and text_list[i+1] == "Mietzins":
				paragraph_list.append(element + " " + text_list[i + 1])
				del text_list[i + 1]
			elif element.startswith(match) and not element.startswith(match+"-"):
				paragraph_list.append(match)
				paragraph_list.append(element.lstrip(match))
			elif element.startswith("(...)"):
				paragraph_list.append("(...)")
				paragraph_list.append(match)
				paragraph_list.append(element.lstrip("(...)"+match))
			elif element == match:
				paragraph_list.append(element)
			else:
				paragraph_list.append(element)
		else:
			paragraph_list.append(element)
	return paragraph_list


def iterate_files(directory, filetype):
	# fname_list = ['BS_APG_001_AUS-2017-58_2017-07-28', 'BS_APG_001_AUS-2017-58_nodate', 'BS_APG_001_BES-2020-16_2020-09-28', 'BS_APG_001_BES-2020-16_nodate', 'BS_APG_001_HB-2015-32_2015-07-22', 'BS_APG_001_HB-2015-32_nodate', 'BS_APG_001_SB-2012-23_2013-09-04', 'BS_APG_001_SB-2012-23_nodate', 'BS_APG_001_SB-2013-105_2014-01-28', 'BS_APG_001_SB-2013-105_nodate', 'BS_APG_001_SB-2014-78_2019-10-29', 'BS_APG_001_SB-2015-36_2016-03-11', 'BS_APG_001_SB-2015-36_nodate', 'BS_APG_001_SB-2015-52_2019-08-13', 'BS_APG_001_SB-2015-52_nodate', 'BS_APG_001_SB-2018-132_nodate', 'BS_APG_001_SB-2018-25_2018-05-31', 'BS_APG_001_SB-2018-25_nodate', 'BS_APG_001_VD-2013-8_2013-05-15', 'BS_APG_001_VD-2013-8_nodate', 'BS_APG_001_VD-2014-132_2015-01-09', 'BS_APG_001_VD-2014-132_nodate', 'BS_APG_001_VD-2014-191_2015-02-11', 'BS_APG_001_VD-2014-191_nodate', 'BS_APG_001_VD-2014-220_2015-07-20', 'BS_APG_001_VD-2014-220_nodate', 'BS_APG_001_VD-2014-44_2014-05-25', 'BS_APG_001_VD-2014-44_nodate', 'BS_APG_001_VD-2015-31_2015-06-08', 'BS_APG_001_VD-2015-31_nodate', 'BS_APG_001_VD-2016-145_2017-02-27', 'BS_APG_001_VD-2016-145_nodate', 'BS_APG_001_VD-2016-182_2017-01-05', 'BS_APG_001_VD-2016-182_nodate', 'BS_APG_001_VD-2016-75_2016-10-19', 'BS_APG_001_VD-2016-75_nodate', 'BS_APG_001_VD-2017-290_2019-01-15', 'BS_APG_001_VD-2017-290_nodate', 'BS_APG_001_VD-2018-101_2019-05-07', 'BS_APG_001_VD-2018-101_nodate', 'BS_APG_001_VD-2018-20_2018-03-19', 'BS_APG_001_VD-2018-20_nodate', 'BS_APG_001_VD-2018-66_2018-11-08', 'BS_APG_001_VD-2018-66_nodate', 'BS_APG_001_VD-2019-214_2020-05-23', 'BS_APG_001_VD-2019-214_nodate', 'BS_APG_001_VD-2019-235_2020-05-19', 'BS_APG_001_VD-2019-235_nodate', 'BS_APG_001_ZB-2014-23_2014-11-25', 'BS_APG_001_ZB-2014-23_nodate', 'BS_SVG_001_BV-2019-22_2020-06-09', 'BS_SVG_001_BV-2019-22_nodate', 'BS_SVG_001_IV-2016-187_2018-08-15', 'BS_SVG_001_IV-2016-187_nodate', 'BS_SVG_001_IV-2017-125_2018-11-14', 'BS_SVG_001_IV-2017-125_nodate', 'BS_SVG_001_IV-2018-107_2019-05-21', 'BS_SVG_001_IV-2018-107_nodate', 'BS_SVG_001_IV-2018-211_2019-05-07', 'BS_SVG_001_IV-2018-211_nodate', 'BS_SVG_001_IV-2018-59_2018-09-25', 'BS_SVG_001_IV-2018-59_nodate', 'BS_SVG_001_IV-2018-83_2019-05-21', 'BS_SVG_001_IV-2018-83_nodate']
	duplicates = get_duplicates(directory) # from the nodate_duplicate_counter.py file
	for filename in sorted(os.listdir(directory)):
		if filename.endswith(filetype) and filename not in duplicates:
			fname = os.path.join(directory, filename)
			fname_json = os.path.join(directory, filename[:-5] + ".json")
			if filename.endswith("nodate.html"):
				xml_filename = filename.replace("nodate.html", "0000-00-00.xml")
				# if not check_if_duplicate(filename):
				# 	xml_filename = filename.replace("nodate.html", "0000-00-00.xml")
				# else:
				# 	continue
			else:
				xml_filename = filename[:-5] + ".xml"
			full_save_name = os.path.join(SAVE_PATH, xml_filename)
			print("Current file name: ", os.path.abspath(fname), "will be converted into ", xml_filename)
			print("\n")
			with open(fname, "r", encoding="utf-8") as file:  # open html file for reading
				with open(fname_json, "r", encoding="utf-8") as json_file:  # open json file for reading
					loaded_json = json.load(json_file)  #load json
					beautifulSoupText = BeautifulSoup(file.read(), "html.parser")  #read html
					# print(beautifulSoupText)
					text = parse_text(beautifulSoupText)

					# print(text)
					# text_wo_hyphens = remove_hyphens(filtered_paragraph_list)
					# print(text_wo_hyphens)
					# print("\n")
					# clean_text_list = remove_page_breaks(text_wo_hyphens)
					# print("\n")
					# print(clean_text_list)
					# print("\n")
					# print("text:\n")
					# print(text)
					paragraph_list = split_absatznr(text)
					# print("paragraph_list:\n")
					# print(paragraph_list)
					filter_list = list(filter(lambda x: x != "", paragraph_list))
					text = list(filter_list)
					# print(filter_list)

					# building the xml tree
					# text node with attributes
					text_node = ET.Element("text")
					text_node.attrib["id"] = filename[:-5]
					text_node.attrib["author"] = ""
					if "Kopfzeile" in loaded_json.keys():
						text_node.attrib["title"] = loaded_json["Kopfzeile"][0]["Text"].replace('  ', ' ')
					# else:
					# 	text_node.attrib["title"] = get_title(beautifulSoupText)
					text_node.attrib["source"] = "https://entscheidsuche.ch"  # ?
					if "Seiten" in loaded_json.keys():
						text_node.attrib["page"] = loaded_json["Seiten"].replace('  ', ' ')
					else:
						text_node.attrib["page"] = ""
					if "Meta" in loaded_json.keys():
						text_node.attrib["topics"] = loaded_json["Meta"][0]["Text"].replace('  ', ' ').strip()
					else:
						text_node.attrib["topics"] = ""
					text_node.attrib["subtopics"] = ""
					if "Sprache" in loaded_json.keys():
						text_node.attrib["language"] = loaded_json["Sprache"].replace('  ', ' ')
					else:
						text_node.attrib["language"] = loaded_json["Kopfzeile"][0]["Sprachen"].replace('  ', ' ')
					if filename.endswith("nodate.html"):
						text_node.attrib["date"] = "0000-00-00"
						text_node.attrib["year"] = "0000"
						text_node.attrib["decade"] = "0000"
					else:
						text_node.attrib["date"] = loaded_json["Datum"].replace('  ', ' ')
						text_node.attrib["year"] = loaded_json["Datum"][:4]
						text_node.attrib["decade"] = loaded_json["Datum"][:3] + "0"
					text_node.attrib["description"] = loaded_json["Abstract"][0]["Text"].replace('  ', ' ')
					text_node.attrib["type"] = loaded_json["Signatur"].replace('  ', ' ')
					text_node.attrib["file"] = filename
					if "HTML" in loaded_json.keys():
						text_node.attrib["url"] = loaded_json["HTML"]["URL"].replace('  ', ' ')

					# body node with paragraph nodes
					# header_node = ET.SubElement(text_node, "header") # drinlassen?
					body_node = ET.SubElement(text_node, "body")
					for para in filter_list:
						if para.startswith(" "): # so that random whitespaces in the beginning of paragraphs are deleted
							para = para[1:]
						p_node = ET.SubElement(body_node, "p")
						# if para in false_marks:
						# 	p_node.attrib["type"] = "plain_text"
						if re.fullmatch(absatz_pattern, para): # changed to fullmatch seemed better
							p_node.attrib["type"] = "paragraph_mark"
						else:
							p_node.attrib["type"] = "plain_text"
						p_node.text = para
					# pb_node = ET.SubElement(body_node, "pb") # drinlassen?
					# footnote_node = ET.SubElement(text_node, "footnote") # drinlassen?

					# creating/outputting the tree
					tree = ET.ElementTree(text_node)
					tree.write(full_save_name, encoding="UTF-8", xml_declaration=True)  # writes tree to file
					ET.dump(tree)  # shows tree in console
					print("\n\n")



def main():

	iterate_files(PATH_TO_DATA+args.directory, args.type)


if __name__ == "__main__":
	main()