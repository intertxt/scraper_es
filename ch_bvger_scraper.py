# -*- encoding: utf-8 -*-

# use following CLI command:
# python3.10 ch_bvger_scraper.py -p CH_BVGer -s CH_BVGer_clean

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


absatz_pattern = r"^(\s)?[0-9]{1,2}\.([0-9]{1,2}(\.)?)*(\s-\s[0-9]{1,2}\.([0-9]{1,2}(\.)?)*)?"
absatz_pattern2 = r"^(\s)?[0-9]{1,2}\.([0-9]{1,2}(\.)?)*(\s-\s[0-9]{1,2}\.([0-9]{1,2}(\.)?)*)?\s-\s[0-9]{1,2}\.([0-9]{1,2}(\.)?)*(\s-\s[0-9]{1,2}\.([0-9]{1,2}(\.)?)*)?"
absatz_pattern3 = r"^([A-Z]\.(\.?[a-z])*|\d{1,2}((\.\s)|([a-z]{1,3}\.?)|(\s[a-z]\)))|§.*:|[a-z]\)(\s[a-h]{1,2})?|\d{1,2}\.)"
datum_pattern = r"[0-9][0-9]?\.(\s?(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)|([0-9]{2}\.))"
false_marks = []


def split_lines(parsed_text: str) -> List[str]:
    split_lines = [line.strip().replace("     ", " ").replace("\uf02d", "").replace(" ", "").replace("\n", "").replace("   ", " ").replace("  ", " ") for line in parsed_text.split("\n")]
    return split_lines


def get_pages(lines: List[str]) -> str:
    page_pattern_fr = r"Page \d{1,3}"
    page_pattern_it = r"Pagina \d{1,3}"
    page_pattern_de = r"Seite \d{1,3}"
    if detect_lang(lines) == "fr":
        pages = [lines.pop(lines.index(line)).split()[1] for line in lines if re.fullmatch(page_pattern_fr, line.strip())]
    elif detect_lang(lines) == "it":
        pages = [lines.pop(lines.index(line)).split()[1] for line in lines if re.fullmatch(page_pattern_it, line.strip())]
    elif "Seite 3" in lines:
        pages = [lines.pop(lines.index(line)).split()[1] for line in lines if re.fullmatch(page_pattern_de, line.strip())]
    else:
        pages = [lines.pop(lines.index(line)) for line in lines if line.isdigit()]
    # pages = [line[2] if line[3] == " " else line[2:4] for line in pages]
    if pages:
        if pages[0] == "2" or pages[0] == "3": pages[0] = "1"
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

                ### this works for footnotes over multiple lines in SK
                for j in range(1, 10):
                    if lines[i+j]:
                        fn_text += " "+lines[i+j]
                    else: break
                ###

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
    begr_counter = 0
    name_pattern = r"[A-Z]\._+"
    klagerin_pattern = r"[A-Z]\.Klägerin\s\d"
    code_pattern = "[A-Z]-\d{1,5}\/\d{4}"

    for i, line in enumerate(lines):
        line = line.strip()
        # get start of main text
        if ("Erwägungen" in line or "Sachverhalt" in line or "Rekurs" in line or "Regeste" in line or "Faits" in line or "Fatti" in line or "Vu" in line or "Gegenstand" in line or "Oggetto" in line) and sachverhalt_counter == 0:
            clean_lines.append(line.strip())
            sachverhalt_counter += 1
            continue

        if sachverhalt_counter == 0 and line:
            clean_lines.append(line.strip())

        else:
            # filter code pattern
            if re.fullmatch(code_pattern, line):
                continue

            # get footnote reference in text
            elif line and line[0].isdigit() and line[-1].isdigit() and lines[i - 1] and len(line) <= 3:
                if para:
                    clean_lines.append(para.strip())
                    para = ""
                clean_lines.append(line)

            # get Klägerin lines (for HG)
            elif re.fullmatch(klagerin_pattern, line):
                if para:
                    clean_lines.append(para.strip())
                    para = ""
                clean_lines.append(line[:2]+" "+line[2:])

            # match pure paragraph numbers
            elif (re.fullmatch(absatz_pattern, line) or re.fullmatch(absatz_pattern2, line) or re.fullmatch(absatz_pattern3, line)) and not re.fullmatch(datum_pattern, line):
                if para:
                    clean_lines.append(para.strip())
                    para = ""
                clean_lines.append(line)
                pm_counter += 1

            # match paragraph numbers with additional text and split
            elif (re.match(absatz_pattern+"\s", line) or re.match(absatz_pattern2+"\s", line) or re.match(absatz_pattern3+"\s", line)) and not re.match(datum_pattern, line) and not line.endswith("Kammer") and not re.match(name_pattern, line):
                if re.match(absatz_pattern, line):
                    match = re.match(absatz_pattern, line).group(0)
                elif re.match(absatz_pattern2, line):
                    match = re.match(absatz_pattern2, line).group(0)
                else:
                    match = re.match(absatz_pattern3, line).group(0)
                if line.strip(match).strip() and line.strip(match).strip()[0] in ";:)].,":
                    if re.match(r".*\w+-$", line):
                        para += line[:-1]
                    else:
                        para += line + " "
                else:
                    line = match, line.strip(match)
                    # line = line.split(" ", 1)
                    if para:
                        clean_lines.append(para.strip())
                        para = ""
                    clean_lines.append(line[0])
                    if len(line) > 1:
                        para += line[1][:-1] if re.match(r".*\w+-$", line[1]) else line[1]+" "
                    pm_counter += 1

            # remove links which are not visible in pdf
            elif line.startswith("http"):
                continue

            # put "Begründung:" in its own paragraph
            elif line.strip() == "Begründung:" and begr_counter == 0:
                if para:
                    clean_lines.append(para.strip())
                    para = ""
                clean_lines.append(line.strip())
                begr_counter += 1

            # put "Begründung:" in its own paragraph
            elif "Rechtliches" in line or "Auszug aus den Erwägungen:" in line:
                if para:
                    clean_lines.append(para.strip())
                    para = ""
                clean_lines.append(line.strip())

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


def build_xml_tree(filename: str, loaded_json, filter_list: List, footnotes: List[Tuple[str]] | None , pages: List[Tuple[str]] | None):
    """Build an XML-tree."""
    text_node = ET.Element("text")
    text_node.attrib["id"] = filename[:-4]
    text_node.attrib["author"] = ""
    if "Kopfzeile" in loaded_json.keys():
        text_node.attrib["title"] = loaded_json["Kopfzeile"][0]["Text"].strip()
        text_node.attrib["source"] = "https://entscheidsuche.ch"
    text_node.attrib["page"] = pages if pages else ""
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
        text_node.attrib["description"] = loaded_json["Abstract"][0]["Text"].strip()
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
        if footnotes and re.search(fn_ref_pattern, para):
            footnotes_copy = footnotes.copy()
            matches = re.findall(fn_ref_pattern, para)
            for match in matches:
                if match[1] in footnotes_copy:
                    para = re.sub(fr"(?:[a-z]|-|%)({match[1]})(?:\s\w|\.|\))", f"{match[0]} [[{match[1]}]] {match[2]}",
                                  para)
                    del footnotes_copy[match[1]]
            p_node.attrib["type"] = "plain_text"
        elif para in false_marks:
            p_node.attrib["type"] = "plain_text"
        elif re.match(datum_pattern, para):
            p_node.attrib["type"] = "plain_text"
        elif footnotes and para.isdigit():
            fn_node = ET.SubElement(p_node, "fn")
            for num, fn in footnotes:
                if num == para:
                    fn_node.text = f"{num}, {fn}"
                    break
            continue
        elif re.fullmatch(absatz_pattern3, para) or re.fullmatch(absatz_pattern2, para) or re.fullmatch(absatz_pattern, para):
            p_node.attrib["type"] = "paragraph_mark"
        elif para.startswith("<table"):
            p_node.attrib["type"] = "table"
        else:
            p_node.attrib["type"] = "plain_text"
        p_node.text = para.strip()
    body_footnote_node = ET.SubElement(text_node, "body_footnote")
    if footnotes:
        for fn_mark in footnotes:
            p_node = ET.SubElement(body_footnote_node, "p")
            p_node.attrib["type"] = "footnote"
            p_node.text = f"{fn_mark} {footnotes[fn_mark]}"
    tree = ET.ElementTree(text_node)  # creating the tree
    ET.indent(tree, level=0)
    return tree


def detect_lang(lines: List[str]) -> str:
    """Detects language of the string."""
    # print(max(lines))
    # print(sorted(lines, reverse=True)[1])
    # print(sorted(lines, reverse=True)[5])
    return detect(" ".join(lines))
    # if sorted(lines, reverse=True)[1] == "…," or max(lines)[-1].isdigit() or sorted(lines, reverse=True)[1][-1].isdigit() or sorted(lines, reverse=True)[1] == "…":
    #     return detect(max(lines)) if not max(lines) in "§.-$£~" and max(lines) != "…," and max(lines) != "…)." and max(lines) != "…" and max(lines) != '…"' else detect(sorted(lines, reverse=True)[5])
    # else:
    #     return detect(max(lines)) if not max(lines) in "§.-$£~" and max(lines) != "…," and max(lines) != "…)." and max(lines) != '…"' and max(lines) != "…" else detect(sorted(lines, reverse=True)[1])


def main():
    footnotes = None
    pages = None
    counter = 0
    diff_encoded_files = ['CH_BVGE_001_A-6171-2009_2011-01-21.xml', 'CH_BVGE_001_BVGE-2007-10_2007-04-23.xml', 'CH_BVGE_001_BVGE-2007-11_2007-07-12.xml', 'CH_BVGE_001_BVGE-2007-12_2007-04-05.xml', 'CH_BVGE_001_BVGE-2007-13_2007-03-13.xml', 'CH_BVGE_001_BVGE-2007-14_2007-03-06.xml', 'CH_BVGE_001_BVGE-2007-15_2007-03-28.xml', 'CH_BVGE_001_BVGE-2007-16_2007-06-01.xml', 'CH_BVGE_001_BVGE-2007-17_2007-03-26.xml', 'CH_BVGE_001_BVGE-2007-18_2007-08-16.xml', 'CH_BVGE_001_BVGE-2007-19_2007-07-06.xml', 'CH_BVGE_001_BVGE-2007-1_2007-03-07.xml', 'CH_BVGE_001_BVGE-2007-21_2007-07-27.xml', 'CH_BVGE_001_BVGE-2007-22_2007-02-21.xml', 'CH_BVGE_001_BVGE-2007-23_2007-05-03.xml', 'CH_BVGE_001_BVGE-2007-24_2007-04-20.xml', 'CH_BVGE_001_BVGE-2007-25_2007-04-25.xml', 'CH_BVGE_001_BVGE-2007-26_2007-04-26.xml', 'CH_BVGE_001_BVGE-2007-27_2007-06-04.xml', 'CH_BVGE_001_BVGE-2007-28_2007-06-25.xml', 'CH_BVGE_001_BVGE-2007-29_2007-07-12.xml', 'CH_BVGE_001_BVGE-2007-2_2007-02-20.xml', 'CH_BVGE_001_BVGE-2007-30_2007-11-27.xml', 'CH_BVGE_001_BVGE-2007-31_2007-11-09.xml', 'CH_BVGE_001_BVGE-2007-32_2007-08-08.xml', 'CH_BVGE_001_BVGE-2007-33_2007-07-31.xml', 'CH_BVGE_001_BVGE-2007-34_2007-09-20.xml', 'CH_BVGE_001_BVGE-2007-35_2007-05-03.xml', 'CH_BVGE_001_BVGE-2007-36_2007-10-04.xml', 'CH_BVGE_001_BVGE-2007-37_2007-09-17.xml', 'CH_BVGE_001_BVGE-2007-38_2007-05-09.xml', 'CH_BVGE_001_BVGE-2007-39_2007-06-12.xml', 'CH_BVGE_001_BVGE-2007-3_2007-04-16.xml', 'CH_BVGE_001_BVGE-2007-40_2007-08-24.xml', 'CH_BVGE_001_BVGE-2007-41_2007-08-20.xml', 'CH_BVGE_001_BVGE-2007-42_2007-11-07.xml', 'CH_BVGE_001_BVGE-2007-43_2007-09-14.xml', 'CH_BVGE_001_BVGE-2007-44_2007-07-12.xml', 'CH_BVGE_001_BVGE-2007-45_2007-10-26.xml', 'CH_BVGE_001_BVGE-2007-46_2007-11-23.xml', 'CH_BVGE_001_BVGE-2007-47_2007-09-21.xml', 'CH_BVGE_001_BVGE-2007-48_2007-09-05.xml', 'CH_BVGE_001_BVGE-2007-49_2007-10-15.xml', 'CH_BVGE_001_BVGE-2007-4_2007-04-24.xml', 'CH_BVGE_001_BVGE-2007-50_2007-05-25.xml', 'CH_BVGE_001_BVGE-2007-5_2007-05-09.xml', 'CH_BVGE_001_BVGE-2007-6_2007-01-25.xml', 'CH_BVGE_001_BVGE-2007-7_2007-07-11.xml', 'CH_BVGE_001_BVGE-2007-8_2007-07-11.xml', 'CH_BVGE_001_BVGE-2007-9_2007-04-18.xml', 'CH_BVGE_001_BVGE-2008-10_2008-01-08.xml', 'CH_BVGE_001_BVGE-2008-11_2007-12-13.xml', 'CH_BVGE_001_BVGE-2008-12_2008-05-02.xml', 'CH_BVGE_001_BVGE-2008-13_2008-01-28.xml', 'CH_BVGE_001_BVGE-2008-14_2008-04-14.xml', 'CH_BVGE_001_BVGE-2008-15_2008-04-21.xml', 'CH_BVGE_001_BVGE-2008-16_2008-02-26.xml', 'CH_BVGE_001_BVGE-2008-17_2008-02-14.xml', 'CH_BVGE_001_BVGE-2008-18_2008-04-02.xml', 'CH_BVGE_001_BVGE-2008-19_2008-02-15.xml', 'CH_BVGE_001_BVGE-2008-1_2008-02-14.xml', 'CH_BVGE_001_BVGE-2008-20_2008-03-28.xml', 'CH_BVGE_001_BVGE-2008-21_2008-04-01.xml', 'CH_BVGE_001_BVGE-2008-22_2008-01-16.xml', 'CH_BVGE_001_BVGE-2008-23_2008-03-04.xml', 'CH_BVGE_001_BVGE-2008-24_2008-06-04.xml', 'CH_BVGE_001_BVGE-2008-25_2008-04-29.xml', 'CH_BVGE_001_BVGE-2008-26_2008-07-15.xml', 'CH_BVGE_001_BVGE-2008-27_2008-05-28.xml', 'CH_BVGE_001_BVGE-2008-28_2008-05-25.xml', 'CH_BVGE_001_BVGE-2008-29_2007-10-04.xml', 'CH_BVGE_001_BVGE-2008-2_2008-02-14.xml', 'CH_BVGE_001_BVGE-2008-30_2008-04-28.xml', 'CH_BVGE_001_BVGE-2008-31_2008-04-15.xml', 'CH_BVGE_001_BVGE-2008-32_2008-04-30.xml', 'CH_BVGE_001_BVGE-2008-33_2008-05-29.xml', 'CH_BVGE_001_BVGE-2008-34_2008-09-11.xml', 'CH_BVGE_001_BVGE-2008-35_2008-09-25.xml', 'CH_BVGE_001_BVGE-2008-36_2008-03-14.xml', 'CH_BVGE_001_BVGE-2008-37_2007-07-23.xml', 'CH_BVGE_001_BVGE-2008-38_2008-06-23.xml', 'CH_BVGE_001_BVGE-2008-39_2008-07-22.xml', 'CH_BVGE_001_BVGE-2008-3_2008-02-15.xml', 'CH_BVGE_001_BVGE-2008-40_2008-06-25.xml', 'CH_BVGE_001_BVGE-2008-41_2008-06-30.xml', 'CH_BVGE_001_BVGE-2008-42_2008-07-02.xml', 'CH_BVGE_001_BVGE-2008-43_2008-08-19.xml', 'CH_BVGE_001_BVGE-2008-44_2008-07-11.xml', 'CH_BVGE_001_BVGE-2008-45_2008-07-14.xml', 'CH_BVGE_001_BVGE-2008-46_2008-11-04.xml', 'CH_BVGE_001_BVGE-2008-47_2008-11-10.xml', 'CH_BVGE_001_BVGE-2008-48_2008-09-25.xml', 'CH_BVGE_001_BVGE-2008-49_2008-07-16.xml', 'CH_BVGE_001_BVGE-2008-4_2008-01-22.xml', 'CH_BVGE_001_BVGE-2008-50_2008-09-24.xml', 'CH_BVGE_001_BVGE-2008-51_2008-09-02.xml', 'CH_BVGE_001_BVGE-2008-52_2008-09-17.xml', 'CH_BVGE_001_BVGE-2008-53_2008-08-22.xml', 'CH_BVGE_001_BVGE-2008-54_2008-09-26.xml', 'CH_BVGE_001_BVGE-2008-55_2007-09-06.xml', 'CH_BVGE_001_BVGE-2008-56_2007-09-06.xml', 'CH_BVGE_001_BVGE-2008-57_2008-12-23.xml', 'CH_BVGE_001_BVGE-2008-58_2008-11-19.xml', 'CH_BVGE_001_BVGE-2008-59_2008-10-01.xml', 'CH_BVGE_001_BVGE-2008-5_2008-03-14.xml', 'CH_BVGE_001_BVGE-2008-60_2008-07-17.xml', 'CH_BVGE_001_BVGE-2008-61_2008-11-25.xml', 'CH_BVGE_001_BVGE-2008-62_2008-08-08.xml', 'CH_BVGE_001_BVGE-2008-63_2008-10-27.xml', 'CH_BVGE_001_BVGE-2008-64_2008-09-23.xml', 'CH_BVGE_001_BVGE-2008-65_2008-09-02.xml', 'CH_BVGE_001_BVGE-2008-66_2008-07-10.xml', 'CH_BVGE_001_BVGE-2008-6_2008-01-17.xml', 'CH_BVGE_001_BVGE-2008-7_2007-12-06.xml', 'CH_BVGE_001_BVGE-2008-8_2007-03-08.xml', 'CH_BVGE_001_BVGE-2008-9_2007-11-19.xml', 'CH_BVGE_001_BVGE-2009-10_2009-04-15.xml', 'CH_BVGE_001_BVGE-2009-11_2008-09-03.xml', 'CH_BVGE_001_BVGE-2009-12_2009-02-27.xml', 'CH_BVGE_001_BVGE-2009-13_2009-03-06.xml', 'CH_BVGE_001_BVGE-2009-14_2008-10-10.xml', 'CH_BVGE_001_BVGE-2009-15_2009-03-11.xml', 'CH_BVGE_001_BVGE-2009-16_2009-05-05.xml', 'CH_BVGE_001_BVGE-2009-17_2009-02-13.xml', 'CH_BVGE_001_BVGE-2009-18_2009-05-20.xml', 'CH_BVGE_001_BVGE-2009-19_2009-07-02.xml', 'CH_BVGE_001_BVGE-2009-1_2008-01-30.xml', 'CH_BVGE_001_BVGE-2009-20_2009-03-23.xml', 'CH_BVGE_001_BVGE-2009-21_2009-04-15.xml', 'CH_BVGE_001_BVGE-2009-22_2009-02-02.xml', 'CH_BVGE_001_BVGE-2009-23_2009-05-25.xml', 'CH_BVGE_001_BVGE-2009-24_2009-05-29.xml', 'CH_BVGE_001_BVGE-2009-25_2009-03-12.xml', 'CH_BVGE_001_BVGE-2009-26_2009-05-15.xml', 'CH_BVGE_001_BVGE-2009-27_2009-04-06.xml', 'CH_BVGE_001_BVGE-2009-28_2009-07-09.xml', 'CH_BVGE_001_BVGE-2009-29_2009-10-07.xml', 'CH_BVGE_001_BVGE-2009-2_2008-08-07.xml', 'CH_BVGE_001_BVGE-2009-30_2009-03-04.xml', 'CH_BVGE_001_BVGE-2009-31_2009-04-30.xml', 'CH_BVGE_001_BVGE-2009-32_2009-07-31.xml', 'CH_BVGE_001_BVGE-2009-33_2009-05-19.xml', 'CH_BVGE_001_BVGE-2009-34_2009-08-21.xml', 'CH_BVGE_001_BVGE-2009-35_2009-02-12.xml', 'CH_BVGE_001_BVGE-2009-36_2009-02-03.xml', 'CH_BVGE_001_BVGE-2009-37_2008-06-18.xml', 'CH_BVGE_001_BVGE-2009-38_2009-09-14.xml', 'CH_BVGE_001_BVGE-2009-39_2009-07-02.xml', 'CH_BVGE_001_BVGE-2009-3_2009-01-08.xml', 'CH_BVGE_001_BVGE-2009-4_2008-06-09.xml', 'CH_BVGE_001_BVGE-2009-5_2008-08-18.xml', 'CH_BVGE_001_BVGE-2009-6_2008-11-25.xml', 'CH_BVGE_001_BVGE-2009-7_2008-12-16.xml', 'CH_BVGE_001_BVGE-2009-8_2009-05-12.xml', 'CH_BVGE_001_BVGE-2009-9_2008-12-22.xml']

    # used this with adjusted path to get diff_encoded_files list
    # for filename in sorted(os.listdir(PATH_TO_DATA)):
    #     with open(os.path.join(PATH_TO_DATA, filename), "r") as file:
    #         if "���" in file.read():
    #             counter += 1
    #             diff_encoded_files.append(filename)
    # print(diff_encoded_files)
    # print(counter)

    for filename in sorted(os.listdir(PATH_TO_DATA)):
        if filename.endswith("pdf") and filename[:-4]+".xml" in diff_encoded_files: # and "CH_BVGE_001_A-4995-2018_2019-05-06" in filename:
            print(f"The following file is being processed:\n{os.path.join(PATH_TO_DATA, filename)}\n")

            # parse with tika library from separate script
            parsed_text = tika_parse(os.path.join(PATH_TO_DATA, filename))
            
            ### stopped here parsing the strangely encoded files

            # lines = split_lines(parsed_text)
            # pages = get_pages(lines)
            # # footnotes = get_footnotes(lines)
            # clean_text = get_paras(lines)
            #
            # # create new filenames for the xml files
            # if filename.endswith("nodate.html"):
            #     xml_filename = filename.replace("nodate.html", "0000-00-00.xml")
            # else:
            #     xml_filename = filename[:-4] + ".xml"
            #
            # # open json pendant
            # json_name = filename[:-3]+"json"
            # if json_name in sorted(os.listdir(PATH_TO_DATA)):
            #     with open(os.path.join(PATH_TO_DATA, json_name), "r", encoding="utf-8") as json_file:
            #         loaded_json = json.load(json_file)  # load json
            #         tree = build_xml_tree(filename, loaded_json, clean_text, footnotes, pages)  # generates XML treea
            #         tree.write(os.path.join(SAVE_PATH, xml_filename), encoding="UTF-8", xml_declaration=True)  # writes tree to file
            #         ET.dump(tree)  # shows tree in console

            # detect_lang(lines)
            print(parsed_text)
            # print(lines)
            # print(pages)
            # for _ in footnotes:
            #     print(f"{_}\t{footnotes[_]}")
            # print(footnotes)
            # print(clean_text)
            # break


            print("\n===========================================================\n\n")


if __name__ == "__main__":
    main()
