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


parser = argparse.ArgumentParser(description="generate clean XML-files from HTML-files")
parser.add_argument("-p","--path_to_data",type=str,help="directory where all the different data is stored")
parser.add_argument("-d","--directory",type=str,default="CH_BGE",help="current directory for the scraper")
parser.add_argument("-t","--type",type=str, default=".html", help="default filetype (html or pdf usually)")

args = parser.parse_args()

PATH_TO_DATA = args.path_to_data

SAVE_PATH = "/home/admin1/tb_tool/clean_scraper_data/CH_BGE_clean/"

ALLOWED_CLASSES = [['big', 'bold'], "paraatf", "bold", ['center', 'pagebreak'], "artref", "bgeref_id"]

absatz_pattern = r"^(\s)?[0-9]+\.([0-9]+(\.)?)*(\s-\s[0-9]+\.([0-9]+(\.)?)*)?"
absatz_pattern2 = r"^(\s)?[0-9]+\.([0-9]+(\.)?)*(\s-\s[0-9]+\.([0-9]+(\.)?)*)?\s-\s[0-9]+\.([0-9]+(\.)?)*(\s-\s[0-9]+\.([0-9]+(\.)?)*)?"
datum_pattern = r"[0-9][0-9]?\.[\s]{1,2}([A-Z][a-z]+|März)\s[1-9][0-9]{3}"
false_marks = []



def parse_text(parsed_html) -> List[str]:
	"""Get text out of HTML-files."""
	text = []
	for tag in parsed_html.findAll(["div"]):
		if "class" in tag.attrs:
			check = any(item in tag["class"] for item in ALLOWED_CLASSES)
			if check:
				tag_text = unicodedata.normalize("NFKD", tag.get_text().strip().replace("\n", ""))
				text.append(tag_text)
	return text


def get_pages(parsed_html) -> str:
	"""Get page indicators out of HTML-files."""
	page_list = []
	for tag in parsed_html.findAll(["a"]):
		if "name" in tag.attrs:
			if tag["name"].startswith("page"):
				page_list.append(tag["name"].lstrip("page"))
	return page_list[0]+"–"+page_list[-1]


# def split_absatznr(text_list) -> List[str]: ###
# 	"""Split "paragraph_mark" from rest of the text."""
# 	paragraph_list = []
# 	for i, element in enumerate(text_list):
# 		if element == "Fr." and re.match(absatz_pattern, text_list[i+1]):
# 			paragraph_list.append(element+" "+text_list[i+1])
# 			del text_list[i+1]
# 		elif element == '-':
# 			paragraph_list.append(element+" "+text_list[i+1])
# 			del text_list[i+1]
# 		elif re.search(absatz_pattern2, element):
# 			match2 = re.search(absatz_pattern2, element).group(0)
# 			if element.startswith(match2):
# 				paragraph_list.append(match2)
# 				paragraph_list.append(element.lstrip(match2))
# 			elif element == match2:
# 				paragraph_list.append(element)
# 			elif element.startswith("(...)"):
# 				paragraph_list.append("(...)")
# 				paragraph_list.append(match2)
# 				paragraph_list.append(element.lstrip("(...)"+match2))
# 			else:
# 				paragraph_list.append(element)
# 		elif re.search(absatz_pattern, element):
# 			match = re.search(absatz_pattern, element).group(0)
# 			if element.startswith(match) and i+1 < len(text_list) and text_list[i+1] == "Mietzins":
# 				paragraph_list.append(element + " " + text_list[i + 1])
# 				del text_list[i + 1]
# 			elif element.startswith(match) and not element.startswith(match+"-"):
# 				paragraph_list.append(match)
# 				paragraph_list.append(element.lstrip(match))
# 			elif element.startswith("(...)"):
# 				paragraph_list.append("(...)")
# 				paragraph_list.append(match)
# 				paragraph_list.append(element.lstrip("(...)"+match))
# 			elif element == match:
# 				paragraph_list.append(element)
# 			else:
# 				paragraph_list.append(element)
# 		else:
# 			paragraph_list.append(element)
# 	return paragraph_list


def build_xml_tree(filename, loaded_json, pages, filter_list, full_save_name):
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
	if filename.endswith("nodate.html"):
		text_node.attrib["date"] = "0000-00-00"
	else:
		text_node.attrib["date"] = loaded_json["Datum"].replace('  ', ' ')
	text_node.attrib["description"] = loaded_json["Abstract"][0]["Text"][12:]
	text_node.attrib["type"] = loaded_json["Signatur"].replace('  ', ' ')
	text_node.attrib["file"] = filename
	if filename.endswith("nodate.html"):
		text_node.attrib["year"] = "0000"
	else:
		text_node.attrib["year"] = loaded_json["Datum"][:4]
	if filename.endswith("nodate.html"):
		text_node.attrib["decade"] = "0000-00-00"
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
		if para in false_marks:
			p_node.attrib["type"] = "plain_text"
		elif re.fullmatch(absatz_pattern, para):  # changed to fullmatch seemed better
			p_node.attrib["type"] = "paragraph_mark"
		else:
			p_node.attrib["type"] = "plain_text"
		p_node.text = para
	# pb_node = ET.SubElement(body_node, "pb") # drinlassen?
	# footnote_node = ET.SubElement(text_node, "footnote") # drinlassen?
	tree = ET.ElementTree(text_node) # creating the tree
	return tree


def iterate_files(directory, filetype):
	fname_list = []
	for filename in sorted(os.listdir(directory)):
		if filename.endswith(filetype):
			fname = os.path.join(directory, filename)
			fname_json = os.path.join(directory, filename[:-5] + ".json")
			if filename.endswith("nodate.html"):
				xml_filename = filename.replace("nodate.html", "0000-00-00.xml")
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
					# print(beautifulSoupText)
					# print("\n")
					filter_list = list(filter(lambda x: x != "", text))
					text = list(filter_list)
					# print(filter_list)
					pages = get_pages(beautifulSoupText)
					tree = build_xml_tree(filename, loaded_json, pages, filter_list, full_save_name)
					tree.write(full_save_name, encoding="UTF-8", xml_declaration=True)  # writes tree to file
					ET.dump(tree)  # shows tree in console
					print("\n\n")



def main():

	iterate_files(PATH_TO_DATA+args.directory, args.type)


if __name__ == "__main__":
	main()