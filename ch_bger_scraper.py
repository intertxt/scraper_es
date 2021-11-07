#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
parser.add_argument("-d","--directory",type=str,default="CH_BGer",help="current directory for the scraper")
parser.add_argument("-t","--type",type=str, default=".html", help="default filetype (html or pdf usually)")

args = parser.parse_args()

PATH_TO_DATA = args.path_to_data

SAVE_PATH = "/home/admin1/tb_tool/clean_scraper_data/CH_BGer_clean/"

ALLOWED_CLASSES = ["para"]

absatz_pattern = r"^(\s)?[0-9]+\.([0-9]+(\.)?)*(\s-\s[0-9]+\.([0-9]+(\.)?)*)?"
absatz_pattern2 = r"^(\s)?[0-9]+\.([0-9]+(\.)?)*(\s-\s[0-9]+\.([0-9]+(\.)?)*)?\s-\s[0-9]+\.([0-9]+(\.)?)*(\s-\s[0-9]+\.([0-9]+(\.)?)*)?"
absatz_pattern3 = r"([A-D]\.(-|\s[A-D])?(\s[a-z]\))?|\d{1,3}((\.\s)|([a-z]{1,3}\)\.?)|(\s[a-z]\)))|§.*:|[a-z]{1,2}\)(\s[a-z]{1,2}\))?|\d{1,3}\.)"
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
				tag_text = tag_text.replace("  ", "")
				tag_text = tag_text.replace("   ", "")
				tag_text = tag_text.replace("     ", "")
				text.append(tag_text)
	return text


def remove_hyphens(text):
	"""Remove hyphens at the end of lines if they are used as word-splitting-indicators."""
	text_wo_hyphens = []
	for i, elem in enumerate(text):
		if i+1 < len(text) and text[i+1] != "" and text[i+1][0].islower() and elem.endswith("-"):
			text_wo_hyphens.append(elem[:-1])
		elif i+1 < len(text) and elem != "" and text[i+1] != "":
			text_wo_hyphens.append(elem+" ")
		else:
			text_wo_hyphens.append(elem)
	return text_wo_hyphens


def get_paragraphs(text_wo_hyphens) -> List[str]:
	"""Fuse lines to paragraphs."""
	paragraph_list = []
	para = ""
	for i, elem in enumerate(text_wo_hyphens):
		if i < 9 and elem != "":
			paragraph_list.append(elem.strip())
		else:
			if re.match(datum_pattern, elem):
				if para != "" and para[-1] != " ":
					para += " "+elem
				else:
					para += elem
			elif re.match(absatz_pattern, elem):
				match = re.match(absatz_pattern, elem).group(0)
				if elem.startswith(match + "________"):
					if para != "" and para[-1] != " ":
						para += " " + elem
				else:
					paragraph_list.append(para.strip())
					para = ""
					paragraph_list.append(match)
					para += elem[len(match):].strip()
			elif re.match(absatz_pattern3, elem):
				match = re.match(absatz_pattern3, elem).group(0)
				if elem.startswith(match + "________"):
					if para != "" and para[-1] != " ":
						para += " " + elem
				else:
					paragraph_list.append(para.strip())
					para = ""
					paragraph_list.append(match)
					para += " " + elem[len(match):].strip()
			else:
				if para != "" and para[-1] != " ":
					para += " " + elem
				else:
					para += elem
	paragraph_list.append(para.strip())
	return paragraph_list


# def get_pages(parsed_html) -> str:
# 	"""Get page indicators out of HTML-files."""
# 	page_list = []
# 	for tag in parsed_html.findAll(["a"]):
# 		if "name" in tag.attrs:
# 			if tag["name"].startswith("page"):
# 				page_list.append(tag["name"].lstrip("page"))
# 	return page_list[0]+"–"+page_list[-1]


# def split_absatznr(text_list) -> List[str]:
# 	"""Split "paragraph_mark" from rest of the text."""
# 	paragraph_list = []
# 	for i, elem in enumerate(text_list):
# 		if i < 7:
# 			paragraph_list.append(elem)
# 		else:
# 			if re.match(absatz_pattern, elem):
# 				match = re.match(absatz_pattern, elem).group(0)
# 				if elem.startswith(match + "________"):
# 					paragraph_list.append(elem)
# 				else:
# 					paragraph_list.append(match)
# 					paragraph_list.append(elem[len(match):].strip())
# 			elif re.match(absatz_pattern3, elem):
# 				match = re.match(absatz_pattern3, elem).group(0)
# 				if elem.startswith(match+"________"):
# 					paragraph_list.append(elem)
# 				else:
# 					paragraph_list.append(match)
# 					paragraph_list.append(elem[len(match):].strip())
# 			else:
# 				paragraph_list.append(elem)
# 	return paragraph_list



def build_xml_tree(filename, loaded_json, filter_list, full_save_name):
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
		text_node.attrib["page"] = ""
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
	if "Abstract" in loaded_json.keys():
		text_node.attrib["description"] = loaded_json["Abstract"][0]["Text"]
	else:
		text_node.attrib["description"] = loaded_json["Kopfzeile"][0]["Text"]
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
		elif re.fullmatch(absatz_pattern3, para) or re.fullmatch(absatz_pattern2, para) or re.fullmatch(absatz_pattern, para) :
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
	for filename in sorted(os.listdir(directory))[245470:]:
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
					loaded_json = json.load(json_file)  # load json
					beautifulSoupText = BeautifulSoup(file.read(), "html.parser")  # read html
					text = parse_text(beautifulSoupText) # parses HTML
					text_wo_hyphens = remove_hyphens(text)
					paragraph_list = get_paragraphs(text_wo_hyphens)
					# print(paragraph_list)
					# text_with_pmarks = split_absatznr(paragraph_list)
					filter_list = list(filter(lambda x: x != ".", paragraph_list))  # removes periods elements
					# print(text_with_pmarks)
					filter_list = list(filter(lambda x: x != "", filter_list)) # removes empty elements
					# filter_list = list(filter(lambda x: x != None, filter_list)) # removes elements of type None
					filter_list = list(filter(lambda x: x != "-", filter_list))  # removes elements of type None
					# pages = get_pages(beautifulSoupText) # extracts pages from HTML file
					#
					tree = build_xml_tree(filename, loaded_json, filter_list, full_save_name) # generates XML tree
					tree.write(full_save_name, encoding="UTF-8", xml_declaration=True)  # writes tree to file
					ET.dump(tree) # shows tree in console
					print("\n\n")


def main():

	iterate_files(PATH_TO_DATA+args.directory, args.type)


if __name__ == "__main__":
	main()