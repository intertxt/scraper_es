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



parser = argparse.ArgumentParser(description='extract text from entscheidsuche.ch')
parser.add_argument('-p','--path_to_data',type=str,help="directory where all the different data is stored")
parser.add_argument('-d','--directory',type=str,default='AG_Gerichte',help='current directory for the scraper')
parser.add_argument('-t','--type',type=str, default=".html", help="default filetype (html or pdf usually)")

args = parser.parse_args()

ALLOWED_CLASSES = ["ft1","ft4","ft3","ft5", 'ft6', 'ft7', 'text', 'ft2', 'ft8', 'ft9', 'ft10']

PATH_TO_DATA = args.path_to_data

SAVE_PATH = '/home/admin1/tb_tool/clean_scraper_data/AG_Gerichte_clean/'

# absatz_pattern = r'^[0-9]+\.([0-9]+(\.)?)*(\s-\s[0-9]+\.([0-9]+(\.)?)*)?'
# absatz_pattern2 = r'^(\s)?[0-9]+\.([0-9]+(\.)?)*(\s-\s[0-9]+\.([0-9]+(\.)?)*)?\s?-\s?[0-9]+\.([0-9]+(\.)?)*(\s-\s[0-9]+\.([0-9]+(\.)?)*)?'
# datum_pattern = r'[0-9][0-9]?\.[\s]{1,2}([A-Z][a-z]+|März)\s[1-9][0-9]{3}'
# title_names = ['Aus den Erwägungen', 'Sachverhalt']
# art_structure = r"\d{1,3}\s?Art\.\s?\d{1,3}\s?"
pm_pattern = r"^([1-9]\.)([1-9]\.?)*(\s-\s([1-9]\.?)+)?"
pm_pattern2 = r"^(\s?[a-f]{1,3}\))+"


def parse_text(parsed_html):
	text_list = []
	for tag in parsed_html.findAll(["table", "span"]):
		if tag.name == "table":
			text_list.append(str(tag))
			tag.clear()
		else:
			attribute = tag.attrs
			if ("class", ["year"]) not in attribute.items() and ("class", ["page_no"]) not in attribute.items() :
				text_list.append(unicodedata.normalize('NFKD', tag.get_text(strip=True)).replace("  ", " "))
	return text_list

	# text = ''
	# for tag in parsed_html.findAll(["span", 'br']):
	# 	if tag.name == 'br':
	# 		text = text + '  '
	# 	else:
	# 		check = any(item in tag["class"] for item in ALLOWED_CLASSES)  # ["class"] is a list
	# 		if check:
	# 			text = text + tag.get_text()
	# return text


def remove_hyphens_at_linebreaks(text) -> List[str]:
	text_wo_hyphens = []
	for i, line in enumerate(text):
		line.strip()
		if line.startswith("<table"):
			text_wo_hyphens.append(line)
		elif len(text) >= i+2 and len(line) >= 2 and line.endswith("-") and line[-2].isalpha and text[i+1][0].islower:
			text_wo_hyphens.append(line[:-1])
		else:
			text_wo_hyphens.append(line+" ")
	return text_wo_hyphens
	
	# lines = text.split('  ')
	# for i, line in enumerate(lines):
	# 	line = line.strip(' ')
	# 	if line.endswith('-') and lines[i + 1] != '' and lines[i + 1][0].islower():
	# 		text_wo_hyphens.append(lines[i][:-1])
	# 	elif line.endswith('-') and lines[i+1] != '' and lines[i + 1][0].isnumeric():
	# 		text_wo_hyphens.append(lines[i]+ ' ' + lines[i+1])
	# 	elif line.endswith('-') and lines[i + 1] == '' and lines[i + 2] != '' and lines[i + 2][0].islower():  # if word is split up at page break
	# 		text_wo_hyphens.append(lines[i][:-1])  # if word is split up at page break
	# 		del lines[i + 1]  # if word is split up at page break
	# 	elif line.endswith('vgl.') and lines[i + 1] == '':  # if word is split up at page break
	# 		text_wo_hyphens.append(lines[i] + ' ')  # if word is split up at page break
	# 		del lines[i + 1]  # if word is split up at page break
	# 	elif line.endswith('Ziff.') and lines[i + 1][0].isnumeric():
	# 		text_wo_hyphens.append(line + ' ' + lines[i + 1])
	# 		del lines[i + 1]
	# 	elif line != '' and line[-1].isalpha() and lines[i + 1] == '':  # if sentence is split up at page break
	# 		text_wo_hyphens.append(lines[i] + ' ')  # if sentence is split up at page break
	# 		del lines[i + 1]  # if sentence is split up at page break
	# 	elif line != '' and 0 <= i + 1 < len(lines) and re.match(r'[0-9][0-9]?\.$', line) and lines[i + 1] != '' \
	# 			and re.match(r'^(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)',
	# 						 lines[i + 1]):  # for dates that are split up otherwise
	# 		text_wo_hyphens.append(lines[i] + ' ' + lines[i + 1] + ' ')
	# 		del lines[i + 1]
	# 	elif line.endswith('-') and lines[i+1] == '' and lines[i + 2].startswith('KABA'):
	# 		text_wo_hyphens.append(lines[i][:-1])
	# 		del lines[i + 1]
	# 	elif line.endswith('-') and lines[i+1] == '' and lines[i + 2].startswith('WAL'):
	# 		text_wo_hyphens.append(lines[i][:-1])
	# 		del lines[i + 1]
	# 	elif line.endswith('-') and lines[i+1] == '' and lines[i + 2][0].isnumeric():
	# 		text_wo_hyphens.append(lines[i]+ ' ' + lines[i+2])
	# 		del lines[i+1]
	# 		del lines[i+2]
	# 	elif line == lines[-1]:
	# 		text_wo_hyphens.append(line)
	# 	else:
	# 		text_wo_hyphens.append(line + ' ')
	#return text_wo_hyphens


def get_paragraphs(text_wo_hyphens):
	paragraph_list = []
	para = ''
	for line in text_wo_hyphens:
		if line.startswith("<table"):
			if para:
				paragraph_list.append(para.strip())
				para = ""
			paragraph_list.append(line)
		elif re.match(pm_pattern, line):
			match = re.match(pm_pattern, line).group(0)
			if re.match(("(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember|Kammer)"),line[len(match)+1:]):
				para += line
			else:
				if para:
					paragraph_list.append(para.strip())
					para = ""
				paragraph_list.append(match)
				if line[len(match):] != " ":
					para += line[len(match):]
		elif re.match(pm_pattern2, line):
			match = re.match(pm_pattern2, line).group(0)
			if para:
				paragraph_list.append(para.strip())
				para = ""
			paragraph_list.append(match)
			if line[len(match):] != " ":
				para += line[len(match):]
		else:
			para += line
	paragraph_list.append(para.strip())
	return paragraph_list

	# for i, element in enumerate(text_wo_hyphens):
	# 	if element.startswith('Sachverhalt') or element.startswith('Aus den Erwägungen'):
	# 		paragraph_list.append(element[:-1])
	# 	elif re.match(art_structure, element):
	# 		paragraph_list.append(element[:-1])
	# 	elif element != '' and element[0].isalpha():
	# 		para += element
	# 	elif element != '' and element[0] in '+/()""§-–[]{}.·':  # because all lines starting with these chars are skipped otherwise
	# 		para += element
	# 	elif element != '' and re.match(datum_pattern, element):
	# 		para += element
	# 	elif element != '' and re.match(r'[0-9][0-9]?\. Auflage', element):
	# 		para += element
	# 	elif element != '' and re.search(absatz_pattern2, element):
	# 		match = re.search(absatz_pattern2, element).group(0)
	# 		if element.startswith(match) and element.endswith(match):
	# 			paragraph_list.append(para[:-1])
	# 			para = ''
	# 			paragraph_list.append(element[:-1])
	# 		elif re.match(r'[0-9][0-9]?\.[\s]{1,2}([A-Z][a-z]+|März)\s?', element):
	# 			para += element
	# 		elif para.startswith(match+')'):
	# 			para += element
	# 		else:
	# 			paragraph_list.append(para[:-1])
	# 			para = ''
	# 			paragraph_list.append(match)
	# 			element = element.replace(match, '')
	# 			para += element
	# 	elif element != '' and re.match(absatz_pattern, element):
	# 		match = re.match(absatz_pattern, element).group(0)
	# 		if element.startswith(match) and element.endswith(match):
	# 			paragraph_list.append(para[:-1])
	# 			para = ''
	# 			paragraph_list.append(element[:-1])
	# 		elif re.match(r'[0-9][0-9]?\.[\s]{1,2}([A-Z][a-z]+|März)\s?', element):
	# 			para += element
	# 		elif element.startswith(match+')'):
	# 			para += element
	# 		else:
	# 			paragraph_list.append(para[:-1])
	# 			para = ''
	# 			paragraph_list.append(match)
	# 			element = element.replace(match, '')
	# 			para += element
	# 	elif element != '' and element[0].isdigit():
	# 		para += element
	# 	else:
	# 		paragraph_list.append(para[:-1])
	# 		para = ''
	return paragraph_list


def get_pages(parsed_html) -> str:
	pages = []
	for tag in parsed_html.findAll('span'):
		if 'page_no' in tag['class']:
			pages.append(tag.text)
	return pages[0] + '-' + pages[-1]


def get_title(parsed_html) -> str:
	for tag in parsed_html.findAll('span'):
		if 'title' in tag['class']:
			return tag.text


def iterate_files(directory, filetype):
	for filename in sorted(os.listdir(directory))[13000:]:  #remove indexing when script is ready for all files
		if filename.endswith(filetype):
			fname = os.path.join(directory, filename)
			fname_json = os.path.join(directory, filename[:-5] + '.json')
			xml_filename = filename[:-5] + '.xml'
			full_save_name = os.path.join(SAVE_PATH, xml_filename)
			print("Current file name: ", os.path.abspath(fname), 'will be converted into ', xml_filename)
			print('\n')
			with open(fname, 'r') as file:
				with open(fname_json, 'r', encoding='utf-8') as json_file:
					loaded_json = json.load(json_file)
					beautifulSoupText = BeautifulSoup(file.read(), 'html.parser')
					text = parse_text(beautifulSoupText)
					# print(text)
					filter_list = filter(lambda x: x != "", text)  # removes empty list elements
					filter_list = list(filter_list)  # removes empty list elements
					# print(filter_list)
					text_wo_hyphens = remove_hyphens_at_linebreaks(text)
					# print(text_wo_hyphens)
					# print(len(text), len(text_wo_hyphens))
					paragraph_list = get_paragraphs(text_wo_hyphens)
					filter_list = filter(lambda x: x != "", paragraph_list)  # removes empty list elements
					filtered_paragraph_list = list(filter_list)  # removes empty list elements
					# print(paragraph_list)
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
					text_node.attrib['page'] = get_pages(beautifulSoupText)
					if 'Meta' in loaded_json.keys():
						text_node.attrib['topics'] = loaded_json['Kopfzeile'][0]['Text']

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
					for para in filtered_paragraph_list:
						# if para.startswith(' '): # so that random whitespaces in the beginning of paragraphs are deleted
						# 	para = para[1:]
						p_node = ET.SubElement(body_node, 'p')
						if re.match(pm_pattern, para) or re.match(pm_pattern2, para):
							p_node.attrib['type'] = 'paragraph_mark'
						else:
							p_node.attrib['type'] = 'plain_text'
						p_node.text = para
					# pb_node = ET.SubElement(body_node, 'pb') # drinlassen?
					# footnote_node = ET.SubElement(text_node, 'footnote') # drinlassen?

					# creating/outputting the tree
					tree = ET.ElementTree(text_node)
					tree.write(full_save_name, encoding='UTF-8', xml_declaration=True)  # writes tree to file
					ET.dump(tree)  # shows tree in console
					print('\n\n')

def main():

	iterate_files(PATH_TO_DATA+args.directory, args.type)


if __name__ == '__main__':
	main()