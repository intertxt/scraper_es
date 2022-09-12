# -*- encoding: utf-8 -*-

# use following CLI command:
# python3.10 sz_gerichte_scraper.py -p SZ_Gerichte -s SZ_Gerichte_clean

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
from langdetect import detect


arg_parser = argparse.ArgumentParser(description="extract Text from PDF-files")
arg_parser.add_argument("-p", "--path_to_data", type=str, help="path to the folder containing PDFs")
arg_parser.add_argument("-s", "--save_folder", type=str, help="name of the folder where the text is to be saved")

args = arg_parser.parse_args()


PATH_TO_DATA = "/home/admin1/tb_tool/scraping_data/"+args.path_to_data # Gerichtname
SAVE_PATH = "/home/admin1/tb_tool/clean_scraper_data/"+args.save_folder # Gerichtname_clean


absatz_pattern = r"^(((\s)?[0-9]{1,2}\.(\/)?)?((\s)?[a-z]\))+|[0-9]{1,2}\.(\/)?([0-9]{1,2}(\.)?)*)\s"
absatz_pattern2 = r"^[0-9]{1,2}\.(\/)?([0-9]{1,2}(\.)?)*\s"
absatz_pattern3 = r"^((\s)?[A-Z]\.(\/)?((\s)?[a-z])*|[IVD]{1,4}\.)\s"
datum_pattern = r"[0-9][0-9]?\.(\s?(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)|([0-9]{2}\.))"
false_marks = []

def split_lines(parsed_text: str) -> List[str]:
    split_lines = [line.strip().replace("     ", " ").replace("\uf02d", "").replace(" ", "").replace("\xa0\xa0\xa0\xa0\xa0\xa0", "").replace("\xa0", "") for line in parsed_text.split("\n")]
    return split_lines


def get_pages(lines: List[str]) -> str | None:
    page_pattern = r"Kantonsgericht\sSchwyz\s\d{1,3}"
    pages = [lines.pop(lines.index(line)).rsplit(" ")[-1] for line in lines if re.fullmatch(page_pattern, line)]
    if pages:
        if pages[0] == "2": pages[0] = "1"
        return f"{pages[0]}–{pages[-1]}"
    else:
        return ""


def get_footnotes(lines: List[str]) -> dict[str: str]:
    footnotes = {}
    fn_pattern = r"^\d{1,2}\s\w*"
    last_num = 0
    for i, line in enumerate(lines):
        if re.match(fn_pattern, line):
            if not footnotes and line.split(" ", 1)[0] == "1":
                fn_num = line.split(" ", 1)[0]
                fn_text = line.split(" ", 1)[1]
            elif footnotes and line.split(" ", 1)[0].isdigit():
                fn_num = line.split(" ", 1)[0]
                fn_text = line.split(" ", 1)[1]
            else:
                continue
            if int(fn_num) - 1 == last_num:
                footnotes[fn_num] = fn_text
                last_num = int(fn_num)
                lines[i] = ""
                # if not lines[i+1]:
                #     footnotes[fn_num] = fn_text
                #     last_num = int(fn_num)
                # elif lines[i+1] and lines[i+1].isdigit():
                #     footnotes[fn_num] = fn_text
                #     last_num = int(fn_num)
                # elif lines[i+1] and lines[i+1].split(" ", 1)[0].isdigit() and int(lines[i+1].split(" ", 1)[0])-1 != last_num:
                #     footnotes[fn_num] = fn_text
                #     last_num = int(fn_num)
                # else:
                #     fn_text += lines[1]


    return footnotes


def get_paras(lines: List[str]) -> List[str]:
    clean_lines = []
    para = ""
    pm_counter = 0
    sachverhalt_counter = 0
    headnote_counter = 0

    for i, line in enumerate(lines):
        line = line.strip()

        # get start of main text
        if  ("nachdem sich ergeben" in line or "Sachverhalt" in line):
            clean_lines.append(line.strip())
            sachverhalt_counter += 1
            continue

        if sachverhalt_counter == 0 and line:
            clean_lines.append(line.strip())

        else:
            # # get footnote reference in text
            # if line and line[0].isdigit() and line[-1].isdigit() and lines[i - 1]:
            #     if para:
            #         clean_lines.append(para.strip())
            #         para = ""
            #     clean_lines.append(line)

            # match pure paragraph numbers
            if (re.fullmatch(absatz_pattern[:-2], line) or re.fullmatch(absatz_pattern2[:-2], line) or re.fullmatch(absatz_pattern3[:-2], line)) and not re.fullmatch(datum_pattern, line) and not re.match("^\w\._+", line):
                if para:
                    clean_lines.append(para.strip())
                    para = ""
                clean_lines.append(line)
                pm_counter += 1

            # match paragraph numbers with additional text and split
            elif (re.match(absatz_pattern, line) or re.match(absatz_pattern2, line) or re.match(absatz_pattern3, line)) and not re.match(datum_pattern, line) and not line.endswith("Kammer") and not re.match("^\w\._+", line) and ((lines[i-1] or lines[i-2] or lines[i-3]) and (lines[i-1] or lines[i-2] or lines[i-3])[-1] != ",") and not (para.strip().endswith("Ziff.") or para.strip().endswith("(U-act.") or para.strip().endswith("und") or para.strip().endswith(";")):
                if re.match(absatz_pattern, line): match = re.match(absatz_pattern, line).group(0)
                elif re.match(absatz_pattern2, line): match = re.match(absatz_pattern2, line).group(0)
                else: match = re.match(absatz_pattern3, line).group(0)
                # line = line.split(" ", 1)
                if para:
                    clean_lines.append(para.strip())
                    para = ""
                clean_lines.append(match.strip())
                # if len(line) > 1:
                para += line[len(match):] if re.match(r".*\w+-$", line[1]) else line[len(match):]+" "
                pm_counter += 1

            # remove links which are not visible in pdf
            elif line.startswith("http"):
                continue

            # remove hyphens at the end of lines if next text is lowercased
            elif line:
                if re.match(r".*\w+-$", line):
                    para += line[:-1]
                else:
                    para += line+" "

    # if para is not an empty string it is appended to the clean_lines list
    if para:
        clean_lines.append(para.strip())
        para = "" 

    return clean_lines


def build_xml_tree(filename: str, loaded_json, filter_list: List, footnotes=None, pages=None):
    """Build an XML-tree."""
    text_node = ET.Element("text")
    text_node.attrib["id"] = filename[:-4]
    text_node.attrib["author"] = ""
    if "Kopfzeile" in loaded_json.keys():
        text_node.attrib["title"] = loaded_json["Kopfzeile"][0]["Text"].strip()
        text_node.attrib["source"] = "https://entscheidsuche.ch"
    if pages:
        text_node.attrib["page"] = pages
    else:
        text_node.attrib["page"] = ""
    if "Meta" in loaded_json.keys():
        text_node.attrib["topics"] = loaded_json["Meta"][0]["Text"][:-1]
    else:
        text_node.attrib["topics"] = ""
    text_node.attrib["subtopics"] = ""
    text_node.attrib["language"] = detect(" ".join(filter_list))
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
    fn_ref_pattern = r"([a-z]|-|%)(\d{1,2})(\s\w|\.|\))"
    for para in filter_list:
        p_node = ET.SubElement(body_node, "p")
        match_indeces = []
        # if footnotes and re.search(fn_ref_pattern, para):
        #     footnotes_copy = footnotes.copy()
        #     matches = re.findall(fn_ref_pattern, para)
        #     for match in matches:
        #         if match[1] in footnotes_copy:
        #             para = re.sub(fr"(?:[a-z]|-|%)({match[1]})(?:\s\w|\.|\))", f"{match[0]} [[{match[1]}]] {match[2]}",
        #                           para)
        #             del footnotes_copy[match[1]]
        #     p_node.attrib["type"] = "plain_text"
        if para in false_marks:
            p_node.attrib["type"] = "plain_text"
        elif re.match(datum_pattern, para):
            p_node.attrib["type"] = "plain_text"
        # elif para.isdigit():
        #     fn_node = ET.SubElement(p_node, "fn")
        #     for num, fn in footnotes:
        #         if num == para:
        #             fn_node.text = f"{num}, {fn}"
        #             break
        #     continue
        elif re.fullmatch(absatz_pattern3[:-2], para) or re.fullmatch(absatz_pattern2[:-2], para) or re.fullmatch(absatz_pattern[:-2], para):
            p_node.attrib["type"] = "paragraph_mark"
        elif para.startswith("<table"):
            p_node.attrib["type"] = "table"
        else:
            p_node.attrib["type"] = "plain_text"
        p_node.text = para.strip()
    body_footnote_node = ET.SubElement(text_node, "body_footnote")
    # for fn_mark in footnotes:
    #     p_node = ET.SubElement(body_footnote_node, "p")
    #     p_node.attrib["type"] = "footnote"
    #     p_node.text = f"{fn_mark} {footnotes[fn_mark]}"
    tree = ET.ElementTree(text_node)  # creating the tree
    ET.indent(tree, level=0)
    return tree


def parse_pdftotree(filename:str) -> list[str]:
    """Parses PDF file input, converts to XML tree via pdftotree library and converts into a list of  strings/line."""
    parsed_text = []
    tree = pdftotree.parse(os.path.join(PATH_TO_DATA, filename))
    # print(tree)
    root = ET.fromstring(tree)
    for div in root.iter("div"):
        if div.attrib["class"] == "ocrx_block":
            for elem in div:
                line = ""
                if elem.attrib["class"] == "ocrx_line":
                    for span in elem.iter("span"):
                        # print(span.text)
                        line += " " + span.text
                    # print(line)
                    parsed_text.append(line.strip())
    return parsed_text


def main():
    for filename in sorted(os.listdir(PATH_TO_DATA)):
        if filename.endswith("pdf"): # and (filename.startswith("SZ_KG_001_ZK1-2011-34_2012-06-12") or filename.startswith("SZ_KG_002_ZK2-2020-84_2021-03-03") or filename.startswith("SZ_KG_003_STK-2013-22_2013-09-03") or filename.startswith("SZ_KG_004_BEK-2014-210_2015-01-29") or filename.startswith("SZ_KG_999_GPR-2017-12_2017-12-13")):
            print(f"The following file is being processed:\n{os.path.join(PATH_TO_DATA, filename)}\n")

            # parse with tika library from separate script
            parsed_text = tika_parse(os.path.join(PATH_TO_DATA, filename))

            # parse with pdftotree library
            # lines = parse_pdftotree(filename)

            lines = split_lines(parsed_text)

            pages = get_pages(lines)
            # footnotes = get_footnotes(lines)
            clean_text = get_paras(lines)

            # create new filenames for the xml files
            if filename.endswith("nodate.html"):
                xml_filename = filename.replace("nodate.html", "0000-00-00.xml")
            else:
                xml_filename = filename[:-4] + ".xml"

            # # open json pendant
            json_name = filename[:-3]+"json"
            if json_name in sorted(os.listdir(PATH_TO_DATA)):
                with open(os.path.join(PATH_TO_DATA, json_name), "r", encoding="utf-8") as json_file:
                    loaded_json = json.load(json_file)  # load json
                    tree = build_xml_tree(filename, loaded_json, clean_text, pages=pages)  # generates XML tree
                    tree.write(os.path.join(SAVE_PATH, xml_filename), encoding="UTF-8", xml_declaration=True)  # writes tree to file
                    ET.dump(tree)  # shows tree in console

            # print(parsed_text)
            # print(lines)
            # print(pages)
            # for _ in footnotes:
            #     print(f"{_}\t{footnotes[_]}")
            # print(footnotes)
            # print(clean_text)



            print("\n===========================================================\n\n")


if __name__ == "__main__":
    main()
