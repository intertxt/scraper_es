#!/usr/bin/env python
# coding: utf-8
# scraper for AG_Gerichte

from bs4 import BeautifulSoup
import os
import argparse
from typing import List
import xml.etree.ElementTree as ET
import json
import re
import unicodedata


parser = argparse.ArgumentParser(description='generate clean XML-files from HTML-files')
parser.add_argument('-p','--path_to_data',type=str,help="directory where all the different data is stored")
parser.add_argument('-d','--directory',type=str,default='BL_Gerichte',help='current directory for the scraper')
parser.add_argument('-t','--type',type=str, default=".html", help="default filetype (html or pdf usually)")

args = parser.parse_args()

PATH_TO_DATA = args.path_to_data

SAVE_PATH = '/home/admin1/tb_tool/clean_scraper_data/BL_Gerichte_clean/'

absatz_pattern = r'^[0-9]+\.([0-9]+(\.)?)*(\s-\s[0-9]+\.([0-9]+(\.)?)*)?'
datum_pattern = r'[0-9][0-9]?\.[\s]{1,2}([A-Z][a-z]+|März)\s[1-9][0-9]{3}'


def parse_text(parsed_html) -> List[str]:
	"""Get text out of HTML-files."""
	invalid_tags = ['sup']
	text = []
	for tag in parsed_html.findAll(["p", 'td', 'strong']):
		for child in tag.findAll(invalid_tags):
			child.decompose()
		text.append(unicodedata.normalize('NFKD', tag.get_text()).strip('\n        ').replace('\n         \n         ', ' '))
	return text


def remove_hyphens(old_text) -> List[str]:
	"""Removes hyphens and merge elements."""
	text_wo_hyphens = []
	text = ''
	for i, para in enumerate(old_text):
		if para.endswith('-') and old_text[i+1][0].islower:
			text_wo_hyphens.append(para[:-1]+old_text[i+1])
			del old_text[i+1]
		else:
			text_wo_hyphens.append(para)
	return text_wo_hyphens


def remove_page_breaks(text_wo_hyphens) -> List[str]:
	""""Remove page breaks and merge elements."""
	# text_list2 = []
	# text2 = ''
	# for i, para in enumerate(text_list):
	# 	if i+1 < len(text_list) and para[:-1] not in '.!?:)0987654321':
	# 		text_list2.append(para + ' ' + text_list[i + 1])
	# 		del text_list[i+1]
	# 	else:
	# 		text_list2.append(para)
	pass


def split_absatznr(text_list) -> List[str]:
	"""Split 'Absatznummern' from rest of the text."""
	paragraph_list = []
	for i, element in enumerate(text_list):
		if re.match(absatz_pattern, element):
			match = re.match(absatz_pattern, element).group(0)
			if element.startswith(match) and element.endswith(match):
				paragraph_list.append(element)
			elif element.startswith(match):
				paragraph_list.append(match)
				paragraph_list.append(element.lstrip(match))
			elif element.startswith('(...)'):
				paragraph_list.append('(...)')
				paragraph_list.append(match)
				paragraph_list.append(element.lstrip('(...)'+match))
			else:
				paragraph_list.append(element)
		else:
			paragraph_list.append(element)
	return paragraph_list


def iterate_files(directory, filetype):
	for filename in sorted(os.listdir(directory))[:10]:
		if filename.endswith(filetype):
			fname = os.path.join(directory, filename)
			fname_json = os.path.join(directory, filename[:-5] + '.json')
			xml_filename = filename[:-5] + '.xml'
			full_save_name = os.path.join(SAVE_PATH, xml_filename)
			print("Current file name: ", os.path.abspath(fname), 'will be converted into ', xml_filename)
			print('\n')
			with open(fname, 'r', encoding='utf-8') as file:  # open html file for reading
				with open(fname_json, 'r', encoding='utf-8') as json_file:  # open json file for reading
					loaded_json = json.load(json_file)  #load json
					beautifulSoupText = BeautifulSoup(file.read(), 'html.parser')  #read html
					# print(beautifulSoupText)
					text = parse_text(beautifulSoupText)
					# print(text)
					filter_list = filter(lambda x: x != "", text)  # removes empty list elements
					filtered_paragraph_list = list(filter_list)
					text_wo_hyphens = remove_hyphens(filtered_paragraph_list)
					# print(text_list)
					paragraph_list = split_absatznr(text_wo_hyphens)

					# building the xml tree
					# text node with attributes
					text_node = ET.Element('text')
					text_node.attrib['id'] = filename[:-5]
					text_node.attrib['author'] = ''
					if 'Kopfzeile' in loaded_json.keys():
						text_node.attrib['title'] = loaded_json['Kopfzeile'][0]['Text']
					else:
						text_node.attrib['title'] = get_title(beautifulSoupText)
					text_node.attrib['source'] = 'https://entscheidsuche.ch'  # ?
					text_node.attrib['page'] = ''
					if 'Meta' in loaded_json.keys():
						text_node.attrib['topics'] = loaded_json['Meta'][0]['Text']
					else:
						text_node.attrib['topics'] = ''
					text_node.attrib['subtopics'] = ''
					text_node.attrib['language'] = loaded_json['Sprache']
					text_node.attrib['date'] = loaded_json['Datum']
					text_node.attrib['description'] = loaded_json['Abstract'][0]['Text']
					text_node.attrib['type'] = loaded_json['Signatur']
					text_node.attrib['file'] = filename
					text_node.attrib['year'] = loaded_json['Datum'][:4]
					text_node.attrib['decade'] = loaded_json['Datum'][:3]+'0'
					text_node.attrib['url'] = loaded_json['HTML']['URL']

					# body node with paragraph nodes
					# header_node = ET.SubElement(text_node, 'header') # drinlassen?

					body_node = ET.SubElement(text_node, 'body')
					for para in paragraph_list:
						if para.startswith(' '): # so that random whitespaces in the beginning of paragraphs are deleted
							para = para[1:]
						p_node = ET.SubElement(body_node, 'p')
						if re.search(absatz_pattern, para):
							p_node.attrib['type'] = 'Absatznummer'
						else:
							p_node.attrib['type'] = 'plain text'
						p_node.text = para
					# pb_node = ET.SubElement(body_node, 'pb') # drinlassen?
					# footnote_node = ET.SubElement(text_node, 'footnote') # drinlassen?

					# creating/outputting the tree
					tree = ET.ElementTree(text_node)
					tree.write(full_save_name, encoding='UTF-8', xml_declaration=True)  # writes tree to file
					# ET.dump(tree)  # shows tree in console
					print('\n\n')



def main():

	iterate_files(PATH_TO_DATA+args.directory, args.type)


if __name__ == '__main__':
	main()