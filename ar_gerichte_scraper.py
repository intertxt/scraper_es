# -*- encoding: utf-8 -*-

# use following CLI command:
# python3.10 ar_gerichte_scraper.py -p AR_Gerichte -s AR_Gerichte_clean

# import necessary modules
import argparse
import os
from tika import parser
import pdftotree
import xml.etree.ElementTree as ET
from pdf_parser import tika_parse
import pdftotree
import re
from typing import List, Tuple
import json


arg_parser = argparse.ArgumentParser(description="extract Text from PDF-files")
arg_parser.add_argument("-p", "--path_to_data", type=str, help="path to the folder containing PDFs")
arg_parser.add_argument("-s", "--save_folder", type=str, help="name of the folder where the text is to be saved")

args = arg_parser.parse_args()


PATH_TO_DATA = "/home/admin1/tb_tool/scraping_data/"+args.path_to_data # Gerichtname
SAVE_PATH = "/home/admin1/tb_tool/clean_scraper_data/"+args.save_folder # Gerichtname_clean


absatz_pattern = r"^(\s)?[0-9]+\.([0-9]+(\.)?)*(\s-\s[0-9]+\.([0-9]+(\.)?)*)?(\s|$)"
absatz_pattern2 = r"^(\s)?[0-9]+\.([0-9]+(\.)?)*(\s-\s[0-9]+\.([0-9]+(\.)?)*)?\s-\s[0-9]+\.([0-9]+(\.)?)*(\s-\s[0-9]+\.([0-9]+(\.)?)*)?(\s|$)"
absatz_pattern3 = r"^([A-D]\.(-|\s[A-D])?(\s[a-z]\))?|\d{1,3}((\.\s)|([a-z]{1,3}\)\.?)|(\s[a-z]\)))|§.*:|[a-z]{1,2}\)(\s[a-z]{1,2}\))?|\d{1,3}\.(\s|$))"
datum_pattern = r"[0-9][0-9]?\.(\s?(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)|([0-9]{2}\.))"
false_marks = []

def split_lines(parsed_text: str) -> List[str]:
    split_lines = [line.strip().replace("     ", " ").replace("\uf02d", "").replace("            ", "").replace("……………...", "").replace("……… ", "").replace("   ", " ") for line in parsed_text.split("\n")]
    return split_lines

def get_pages(lines: List[str]) -> str:
    pages = [lines.pop(lines.index(line)) for line in lines if line.startswith("Seite") and line[-1].isdigit()]
    pages = [line.split(" ") for line in pages]
    if pages:
        if pages[0][1] == "2":
            return "1-"+pages[-1][1]
        else:
            return pages[0][1]+"-"+pages[-1][1]
    else:
        return ""


def remove_hyphens(lines: List[str]) -> List[str]:
    return [line.rstrip("-") if line.endswith("-") else line+" " for line in lines]


def get_footnotes(lines: List[str]) -> dict[str: str]:
    footnotes = {}
    fn_pattern = r"^\d{1,2}\s\s\w*"
    fn_pattern2 = r"^41\s\w*"
    for i, line in enumerate(lines):
        if re.match(fn_pattern, line) or re.match(fn_pattern2, line):
            # footnotes.append(fn[:2].strip())
            counter = 0
            fn_parts = []
            if lines and lines[i+counter] and len(lines[i+counter])>1:
                while not lines[i+counter].endswith("."):
                    fn_parts.append(lines[i+counter])
                    lines[i+counter] = ""
                    counter += 1
                fn_parts.append(lines[i+counter])
                lines[i + counter] = ""
                fn_parts = [line.strip("-") for line in fn_parts] # removes trailing hyphens
                if re.match(fn_pattern2, line):
                    fn_entry = "".join(fn_parts).split(" ", 1)
                else:
                    if "  " in "".join(fn_parts):
                        fn_entry = "".join(fn_parts).split("  ")
                    else:
                        fn_entry = "".join(fn_parts).split(" ")
                footnotes[fn_entry[0]] = fn_entry[1]
                lines[i] = ""
    return footnotes


def get_paras(lines: List[str]) -> List[str]:
    counter = 0
    para = ""
    clean_lines = []
    fn_ref_pattern = r"([a-z]|-|%)(\d{1,2})(\s\w|\.|\))"
    for i, line in enumerate(lines):
        line = line.strip()
        if line:
        # match pure paragraph numbers
            if (re.fullmatch(absatz_pattern, line) or re.fullmatch(absatz_pattern2, line) or re.fullmatch(absatz_pattern3, line)) and not re.fullmatch(datum_pattern, line):
                if para:
                    clean_lines.append(para.strip())
                    para = ""
                    clean_lines.append(line)
                else:
                    clean_lines.append(line)

           # match paragraph numbers with additional text and split
            elif (re.match(absatz_pattern, line) or re.match(absatz_pattern2, line) or re.match(absatz_pattern3, line)) and not re.match(datum_pattern, line) and not line.endswith("Kammer"):
                split_line = line.split(" ", 1)
                # print(split_line)
                if para:
                    clean_lines.append(para.strip())
                    para = ""
                    for elem in split_line[1:]:
                        if elem.endswith("-"):
                            para += elem[:-1]
                        else:
                            para += elem+" "
                else:
                    for elem in split_line[1:]:
                        if elem.endswith("-"):
                            para += elem[:-1]
                        else:
                            para += elem+" "
                clean_lines.append(split_line[0])
                
        # get footnote reference in text
            elif re.search(fn_ref_pattern, line):
                matches = [match[1] for match in re.findall(fn_ref_pattern, line)]
                for match in matches:
                    line = line.replace(match, "")
                if line.endswith("-"):
                    para += line[:-1]
                else:
                    para += line+" "
                for match in matches:
                    clean_lines.append(para)
                    para = ""
                    clean_lines.append(match)

            # all other lines/paras
            else:
                if line.endswith("-"):
                    para += line[:-1]
                else:
                    para += line+" "


    # if para is not an empty string it is appended to the clean_lines list
    if para:
        clean_lines.append(para.strip())

    return clean_lines


def build_xml_tree(filename: str, loaded_json, filter_list: List, footnotes: List[Tuple[str]], pages: str):
    """Build an XML-tree."""
    text_node = ET.Element("text")
    text_node.attrib["id"] = filename[:-4]
    text_node.attrib["author"] = ""
    text_node.attrib["page"] = pages
    if "Kopfzeile" in loaded_json.keys():
        text_node.attrib["title"] = loaded_json["Kopfzeile"][0]["Text"].strip()
        text_node.attrib["source"] = "https://entscheidsuche.ch"
    if "Meta" in loaded_json.keys():
        text_node.attrib["topics"] = loaded_json["Meta"][0]["Text"]
    else:
        text_node.attrib["topics"] = ""
    text_node.attrib["subtopics"] = ""
    if "Sprache" in loaded_json.keys():
        text_node.attrib["language"] = loaded_json["Sprache"].replace('  ', ' ')
    else:
        text_node.attrib["language"] = loaded_json["Meta"][0]["Sprachen"][0]
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
        if "-" in loaded_json["Datum"]:
            text_node.attrib["year"] = loaded_json["Datum"][:4]
        else:
            text_node.attrib["year"] = loaded_json["Datum"][-4:]
    if filename.endswith("nodate.html"):
        text_node.attrib["decade"] = "0000-00-00"
    else:
        if "-" in loaded_json["Datum"]:
            text_node.attrib["decade"] = loaded_json["Datum"][:3] + "0"
        else:
            text_node.attrib["decade"] = loaded_json["Datum"][-4:-1] + "0"
    if "HTML" in loaded_json.keys():
        text_node.attrib["url"] = loaded_json["HTML"]["URL"].replace('  ', ' ')
    # body node with paragraph nodes
    # header_node = ET.SubElement(text_node, "header") # drinlassen?
    body_node = ET.SubElement(text_node, "body")
    for para in filter_list:
        p_node = ET.SubElement(body_node, "p")
        if para in false_marks:
            p_node.attrib["type"] = "plain_text"
        elif re.match(datum_pattern, para):
            p_node.attrib["type"] = "plain_text"
        elif footnotes and para.isdigit():
             if para in footnotes:
                 p_node.attrib["type"] = "footnote_mark"
                 p_node.text = para
                 # fn_node = ET.SubElement(p_node, "fn")
                 # fn_node.text = f"{para}, {footnotes[para]}"
                 # continue

        elif re.fullmatch(absatz_pattern3, para) or re.fullmatch(absatz_pattern2, para) or re.fullmatch(absatz_pattern, para):
            p_node.attrib["type"] = "paragraph_mark"
        elif para.startswith("<table"):
            p_node.attrib["type"] = "table"
        else:
            p_node.attrib["type"] = "plain_text"
        p_node.text = para.strip()
    for fn_mark in footnotes:
        p_node = ET.SubElement(text_node, "p")
        p_node.attrib["type"] = "footnote"
        p_node.text = f"{fn_mark} {footnotes[fn_mark]}"
    tree = ET.ElementTree(text_node) # creating the tree
    ET.indent(tree, level=0)
    return tree



def main():
    for filename in sorted(os.listdir(PATH_TO_DATA)):
        if filename.endswith("pdf") and filename.startswith("AR_OG_008_OG-FE3-17-2_2017-04-12"): # and filename[:-4] and filename[:-4] not in os.listdir(SAVE_PATH) and filename not in ["AR_OG_003_OG-O3V-16-32_2017-10-31.pdf", "AR_KG_005_Verwaltung-ARGVP-199_1997-12-04.pdf", "AR_KG_005_Verwaltung-ARGVP-1997-1318_1997-12-04.pdf", "AR_OG_003_OG-O3V-15-31_2016-04-26.pdf"]:
            print(f"The following file is being processed:\n{os.path.join(PATH_TO_DATA, filename)}\n")
            # parse with tika library from separate script
            parsed_text = tika_parse(os.path.join(PATH_TO_DATA, filename))
            # parse with pdftotree library
            # tree = pdftotree.parse(os.path.join(PATH_TO_DATA, filename))
            # print(tree)
            # root = ET.fromstring(tree)
            # for div in root.iter("div"):
            #     if div.attrib["class"] == "ocrx_block":
            #         for span in div.iter("span"):
            #             print(span.text)
            lines = split_lines(parsed_text)
            pages = get_pages(lines)
            footnotes = get_footnotes(lines)
            lines_wo_hyphens = remove_hyphens(lines)
            clean_text = get_paras(lines)
            #
            # create new filenames for the xml files
            if filename.endswith("nodate.html"):
                xml_filename = filename.replace("nodate.html", "0000-00-00.xml")
            else:
                xml_filename = filename[:-4] + ".xml"

            # print(parsed_text)
            # print(lines)
            # print(pages)
            # print(footnotes, len(footnotes))
            # print(lines_wo_hyphens)
            # print(clean_text)

            # open json pendant
            json_name = filename[:-3]+"json"
            if json_name in sorted(os.listdir(PATH_TO_DATA)):
                with open(os.path.join(PATH_TO_DATA, json_name), "r", encoding="utf-8") as json_file:
                    loaded_json = json.load(json_file)  # load json
                    tree = build_xml_tree(filename, loaded_json, clean_text, footnotes, pages)  # generates XML tree
                    tree.write(os.path.join(SAVE_PATH, xml_filename), encoding="UTF-8", xml_declaration=True)  # writes tree to file
                    ET.dump(tree)  # shows tree in console


    
            print("\n===========================================================\n\n")


if __name__ == "__main__":
    main()
