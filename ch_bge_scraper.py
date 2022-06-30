#!/usr/bin/env python
# coding: utf-8
# scraper for BS_Omni

from bs4 import BeautifulSoup, NavigableString, Tag
import os
import argparse
from typing import List
import xml.etree.ElementTree as ET
import json
import re
import unicodedata
from duplicate_checker import get_duplicates
# import dateparser ### install this

# can be run with the following CLI prompt: python3.6 ch_bge_scraper.py -p /home/admin1/tb_tool/scraping_data/


parser = argparse.ArgumentParser(description="generate clean XML-files from HTML-files")
parser.add_argument("-p","--path_to_data",type=str,help="directory where all the different data is stored")
parser.add_argument("-d","--directory",type=str,default="CH_BGE",help="current directory for the scraper")
parser.add_argument("-t","--type",type=str, default=".html", help="default filetype (html or pdf usually)")

args = parser.parse_args()

PATH_TO_DATA = args.path_to_data

SAVE_PATH = "/home/admin1/tb_tool/clean_scraper_data/CH_BGE_clean/"

ALLOWED_CLASSES = [['big', 'bold'], "paraatf", "bold", ['center', 'pagebreak'], "artref", "bgeref_id"]

absatz_pattern = r"^(\s)?[0-9]+(\.)?(\s)?([a-z]\)|([0-9]+(\.)?)*(\s-\s[0-9]+\.([0-9]+(\.)?)*)?)"
absatz_pattern2 = r"^(\s)?[0-9]+\.([0-9]+(\.)?)*(\s-\s[0-9]+\.([0-9]+(\.)?)*)?\s-\s[0-9]+\.([0-9]+(\.)?)*(\s-\s[0-9]+\.([0-9]+(\.)?)*)?"
absatz_pattern3 = r"([A-Z]([IVCMD]+)?(\.|\))-?(\s[a-z]\))?|(\s*[a-z]{1,3}(\)|\.))+|\d{1,3}((\.\s)|(\s[a-z]\)))|§.*:|[a-z]{1,2}\)(\s[a-z]{1,2}\))?|\d{1,3}\.)"
datum_pattern = r"[0-9][0-9]?\.([\s]{1,2}([A-Z][a-z]+|März)|[0-9]{1,2}\.)\s?[1-9][0-9]{3}"
code = r"^\d{1,3}\s[IVCMD]\s\d{1,3}$"
false_marks = []



def parse_text(parsed_html) -> List[str]:
	"""Get text out of HTML-files."""
	text = []
	for tag in parsed_html.findAll(["div", "br"]):
		if "class" in tag.attrs:
			check = any(item in tag["class"] for item in ALLOWED_CLASSES)
			if check:
				tag_text = unicodedata.normalize("NFKD", tag.get_text().strip().replace("\n", ""))
				text.append(tag_text)
		else: # extracts text in between breaks
			next_s = tag.nextSibling
			if not (next_s and isinstance(next_s, NavigableString)):
				continue
			next2_s = next_s.nextSibling
			if next2_s and isinstance(next2_s, Tag) and next2_s.name == 'br':
				br_text = unicodedata.normalize("NFKD", next_s.strip())
				text.append(br_text)
	return text


def get_dates():
	"""Extract dates and times (with timeit) from HTML text """
	# return dateparser.parse("27. August 2016")
	pass # try again after installing module else try with regex


def get_pages(parsed_html) -> str:
	"""Get page indicators out of HTML-files."""
	page_list = []
	for tag in parsed_html.findAll(["a"]):
		if "name" in tag.attrs:
			if tag["name"].startswith("page"):
				page_list.append(tag["name"].lstrip("page"))
	return page_list[0]+"–"+page_list[-1]


def get_paragraphs(text_wo_hyphens) -> List[str]:
	"""Separate paragraph_marks from paragraphs."""
	paragraph_list = []
	year = ""
	for i, elem in enumerate(text_wo_hyphens):
		elem = elem.strip()
		if elem.startswith("<table"):
			paragraph_list.append(elem.strip())
		else:
			# if re.match(code, elem.strip()):
			# 	paragraph_list.append(elem)
			# 	year = str(1900 + int(elem.split()[0]) - 26)
			if re.match(datum_pattern, elem):
				paragraph_list.append(elem.strip())
			elif re.match(absatz_pattern, elem):
				match = re.match(absatz_pattern, elem).group(0)
				if elem.startswith(match + "__") or elem.startswith(match + "Abteilung") or elem.startswith(
						match + "Kammer") or elem.startswith(match + "Auszug"):
					paragraph_list.append(elem.strip())
				else:
					paragraph_list.append(match.strip())
					paragraph_list.append(elem[len(match):].strip())
			elif re.match(absatz_pattern3, elem):
				match = re.match(absatz_pattern3, elem).group(0)
				if elem.startswith(match + "__") or elem.startswith(match + "Abteilung") or elem.startswith(
						match + "Kammer") or text_wo_hyphens[i] == text_wo_hyphens[-1] or elem.startswith(
					match + "2"):
					paragraph_list.append(elem.strip())
				else:
					paragraph_list.append(match.strip())
					paragraph_list.append(elem[len(match):].strip())
			else:
				paragraph_list.append(elem.strip())
	return paragraph_list

def build_xml_tree(filename, loaded_json, pages, filter_list, full_save_name, year):
	"""Build an XML-tree."""
	text_node = ET.Element("text")
	text_node.attrib["id"] = filename[:-5]
	text_node.attrib["author"] = ""
	if "Kopfzeile" in loaded_json.keys():
		text_node.attrib["title"] = loaded_json["Kopfzeile"][0]["Text"].replace('  ', ' ')
	text_node.attrib["source"] = "https://entscheidsuche.ch"
	if "Seiten" in loaded_json.keys():
		text_node.attrib["page"] = loaded_json["Seiten"].replace('  ', ' ')
	else:
		text_node.attrib["page"] = pages
	if "Meta" in loaded_json.keys():
		text_node.attrib["topics"] = loaded_json["Meta"][0]["Text"]
	else:
		text_node.attrib["topics"] = ""
	text_node.attrib["subtopics"] = ""
	if "Sprache" in loaded_json.keys():
		text_node.attrib["language"] = loaded_json["Sprache"].replace('  ', ' ')
	else:
		text_node.attrib["language"] = loaded_json["Kopfzeile"][0]["Sprachen"].replace('  ', ' ')
	if filename.endswith("nodate.html") and year:
		text_node.attrib["date"] = year+"-00-00"
	else:
		text_node.attrib["date"] = loaded_json["Datum"].replace('  ', ' ')
	text_node.attrib["description"] = loaded_json["Abstract"][0]["Text"][12:]
	text_node.attrib["type"] = loaded_json["Signatur"].replace('  ', ' ')
	text_node.attrib["file"] = filename
	if filename.endswith("nodate.html"):
		text_node.attrib["year"] = year
	else:
		text_node.attrib["year"] = loaded_json["Datum"][:4]
	if filename.endswith("nodate.html"):
		text_node.attrib["decade"] = year[:-1]+"0"
	else:
		text_node.attrib["decade"] = loaded_json["Datum"][:3] + "0"
	if "HTML" in loaded_json.keys():
		text_node.attrib["url"] = loaded_json["HTML"]["URL"].replace('  ', ' ')
	# body node with paragraph nodes
	# header_node = ET.SubElement(text_node, "header") # drinlassen?
	body_node = ET.SubElement(text_node, "body")
	for para in filter_list:
		if para.startswith(" "):  # so that random whitespaces in the beginning of paragraphs are deleted
			para = para[1:]
		p_node = ET.SubElement(body_node, "p")
		if re.fullmatch(absatz_pattern3, para):  # changed to fullmatch seemed better
			p_node.attrib["type"] = "paragraph_mark"
		else:
			p_node.attrib["type"] = "plain_text"
		p_node.text = para
	# pb_node = ET.SubElement(body_node, "pb") # drinlassen?
	# footnote_node = ET.SubElement(text_node, "footnote") # drinlassen?
	tree = ET.ElementTree(text_node) # creating the tree
	return tree


def iterate_files(directory, filetype):
	duplicates = get_duplicates(directory) # from the nodate_duplicate_counter.py file
	with open("nodates.txt", "r", encoding="utf-8") as nodate_filenames:
		nodate_name_list = [line[2:-14]+"nodate.html" for line in nodate_filenames.read().split("\n")]
		for filename in sorted(os.listdir(directory)):
			if filename.endswith(filetype) and "nodate" in filename and filename in nodate_name_list:
				fname = os.path.join(directory, filename)
				fname_json = os.path.join(directory, filename[:-5] + ".json")
				print("Current file name: ", os.path.abspath(fname))
				with open(fname, "r", encoding="utf-8") as file:  # open html file for reading
					with open(fname_json, "r", encoding="utf-8") as json_file:  # open json file for reading
						loaded_json = json.load(json_file)  #load json
						beautifulSoupText = BeautifulSoup(file.read(), "html.parser")  #read html
						# print(beautifulSoupText)
						text = parse_text(beautifulSoupText)
						# print(text)
						# print(beautifulSoupText)
						# print("\n")
						filter_list = list(filter(lambda x: x != "", text))
						# print(filter_list)
						text_with_pmarks = get_paragraphs(filter_list)
						# print("\n")
						# print(text_with_pmarks)
						filter_list = list(filter(lambda x: x != "", text_with_pmarks))
						# print(filter_list)
						filter_list = list(filter(lambda x: x != None, filter_list))
						# print(filter_list)
						filter_list = list(filter(lambda x: x != ". ", filter_list))
						pages = get_pages(beautifulSoupText)
						# calculate year from formula: 1900 + first number - 26
						year = str(1900 + int(filename.split("_")[3].split("-")[1]) - 26)
						if filename.endswith("nodate.html") and year:
							xml_filename = filename.replace("nodate.html", year + "-00-00.xml")
						else:
							xml_filename = filename[:-5] + ".xml"
						full_save_name = os.path.join(SAVE_PATH, xml_filename)
						print("Current file name: ", os.path.abspath(fname), "will be converted into ", xml_filename)
						print("\n")
						tree = build_xml_tree(filename, loaded_json, pages, filter_list, full_save_name, year)
						tree.write(full_save_name, encoding="UTF-8", xml_declaration=True)  # writes tree to file
						ET.dump(tree)  # shows tree in console
						print("\n\n")


def main():

	iterate_files(PATH_TO_DATA+args.directory, args.type)


if __name__ == "__main__":
	main()