# -*- encoding: utf-8 -*-

# use following CLI command:
# python3.10 zh_obergericht_scraper.py -p ZH_Obergericht -s ZH_Obergericht_clean

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


absatz_pattern = r"^(\s)?[0-9]+\.([0-9]+(\.)?)*(\s-\s[0-9]+\.([0-9]+(\.)?)*)?"
absatz_pattern2 = r"^(\s)?[0-9]+\.([0-9]+(\.)?)*(\s-\s[0-9]+\.([0-9]+(\.)?)*)?\s-\s[0-9]+\.([0-9]+(\.)?)*(\s-\s[0-9]+\.([0-9]+(\.)?)*)?"
absatz_pattern3 = r"([A-D]\.(-|\s[A-D])?(\s[a-z]\))?|\d{1,3}((\.\s)|([a-z]{1,3}\)\.?)|(\s[a-z]\)))|§.*:|[a-z]{1,2}\)(\s[a-z]{1,2}\))?|\d{1,3}\.)"
datum_pattern = r"[0-9][0-9]?\.(\s?(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)|([0-9]{2}\.))"
false_marks = []

def split_lines(parsed_text: str) -> List[str]:
    split_lines = [line.strip().replace("     ", " ").replace("\uf02d", "").replace(" ", "").replace(" ", "") for line in parsed_text.split("\n")]
    return split_lines


def get_pages(lines: List[str]) -> str:
    pages = [lines.pop(lines.index(line)).strip("- ") for line in lines if line.startswith("-") and line.endswith("-")]
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

################ for ZH_BK ###################
def get_paras(lines: List[str]) -> List[str]:
    clean_lines = []
    para = ""
    pm_counter = 0
    sachverhalt_counter = 0

    for i, line in enumerate(lines):
        line = line.strip()
        # get start of main text
        # if line:
        #     if "Sachverhalt" in line or "Faits" in line:
        #         clean_lines.append(line.strip())
        #         sachverhalt_counter += 1
        #         continue
        #
        #     if sachverhalt_counter == 0 and line:
        #         clean_lines.append(line.strip())
        #
        #     else:
        #     get footnote reference in text
        if line and line[0].isdigit() and line[-1].isdigit() and lines[i - 1]:
            if para:
                clean_lines.append(para.strip())
                para = ""
            clean_lines.append(line)

        # match pure paragraph numbers
        elif (re.fullmatch(absatz_pattern, line) or re.fullmatch(absatz_pattern2, line) or re.fullmatch(
                absatz_pattern3, line)) and not re.fullmatch(datum_pattern, line):
            if para:
                clean_lines.append(para.strip())
                para = ""
            clean_lines.append(line)
            pm_counter += 1

        # match paragraph numbers with additional text and split
        elif (re.match(absatz_pattern, line) or re.match(absatz_pattern2, line) or re.match(absatz_pattern3,
                                                                                            line)) and not re.match(
                datum_pattern, line) and not line.endswith("Kammer") and not re.match("[A-Z]\._+", line):
            line = line.split(" ", 1)
            if para:
                clean_lines.append(para.strip())
                para = ""
            clean_lines.append(line[0])
            if len(line) > 1:
                para += line[1][:-1] if re.match(r".*\w+-$", line[1]) else line[1] + " "
            pm_counter += 1

        # remove links which are not visible in pdf
        elif line.startswith("http"):
            continue

        # remove hyphens at the end of lines if next text is lowercased
        elif line:
            if re.match(r".*\w+-$", line):
                para += line[:-1]
            else:
                para += line + " "

    # if para is not an empty string it is appended to the clean_lines list
    if para:
        clean_lines.append(para.strip())
        para = ""

    return clean_lines
#############################################

################ for ZH_HG ###################
def get_paras_hg(lines: List[str]) -> List[str]:
    clean_lines = []
    para = ""
    pm_counter = 0
    sachverhalt_counter = 0



    for i, line in enumerate(lines):
        line = line.strip()
        # get start of main text
        if line:
            if "Erwägung" in line or "Rechtsbegehren" in line or "erwägt" in line or "Sachverhalt" in line or "in Sachen" in line and len(lines) > 50:
                clean_lines.append(line.strip())
                sachverhalt_counter += 1
                continue

            if sachverhalt_counter == 0 and line and len(lines) > 50:
                clean_lines.append(line.strip())

            else:
                # get footnote reference in text
                if line and line[0].isdigit() and line[-1].isdigit() and lines[i - 1]:
                    if para:
                        clean_lines.append(para.strip())
                        para = ""
                    clean_lines.append(line)

                # match pure paragraph numbers
                elif (re.fullmatch(absatz_pattern, line) or re.fullmatch(absatz_pattern2, line) or re.fullmatch(
                        absatz_pattern3, line)) and not re.fullmatch(datum_pattern, line):
                    if para:
                        clean_lines.append(para.strip())
                        para = ""
                    clean_lines.append(line)
                    pm_counter += 1

                # match paragraph numbers with additional text and split
                elif (re.match(absatz_pattern, line) or re.match(absatz_pattern2, line) or re.match(absatz_pattern3,
                                                                                                    line)) and not re.match(
                        datum_pattern, line) and not line.endswith("Kammer") and not re.match("[A-Z]\._+", line):
                    line = line.split(" ", 1)
                    if para:
                        clean_lines.append(para.strip())
                        para = ""
                    clean_lines.append(line[0])
                    if len(line) > 1:
                        para += line[1][:-1] if re.match(r".*\w+-$", line[1]) else line[1] + " "
                    pm_counter += 1

                # remove links which are not visible in pdf
                elif line.startswith("http"):
                    continue

                # remove hyphens at the end of lines if next text is lowercased
                elif line:
                    if re.match(r".*\w+-$", line):
                        para += line[:-1]
                    else:
                        para += line + " "

    # if para is not an empty string it is appended to the clean_lines list
    if para:
        clean_lines.append(para.strip())
        para = ""

    return clean_lines
#############################################

def build_xml_tree(filename: str, loaded_json, filter_list: List, footnotes=None, pages=None):
    """Build an XML-tree."""
    text_node = ET.Element("text")
    text_node.attrib["id"] = filename[:-4]
    text_node.attrib["author"] = ""
    if "Kopfzeile" in loaded_json.keys():
        text_node.attrib["title"] = loaded_json["Kopfzeile"][0]["Text"].strip()
        text_node.attrib["source"] = "https://entscheidsuche.ch"
    text_node.attrib["page"] = pages
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
        elif re.fullmatch(absatz_pattern3, para) or re.fullmatch(absatz_pattern2, para) or re.fullmatch(absatz_pattern, para):
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
    file_list = ['ZH_HG_001_HE110618_2012-03-16', 'ZH_HG_001_HE110762_2012-04-13', 'ZH_HG_001_HE110857_2012-07-18', 'ZH_HG_001_HE110869_2012-07-18', 'ZH_HG_001_HE110966_2012-04-24', 'ZH_HG_001_HE120039_2012-07-10', 'ZH_HG_001_HE120275_2012-07-31', 'ZH_HG_001_HE120289_2012-08-16', 'ZH_HG_001_HE120338_2012-09-24', 'ZH_HG_001_HE120490_2012-12-21', 'ZH_HG_001_HE120518_2013-02-08', 'ZH_HG_001_HE120519_2013-02-12', 'ZH_HG_001_HE120523_2013-01-29', 'ZH_HG_001_HE130001_2013-01-29', 'ZH_HG_001_HE130011_2013-02-12', 'ZH_HG_001_HE130067_2013-03-14', 'ZH_HG_001_HE130196_2013-07-19', 'ZH_HG_001_HE130328_2013-11-26', 'ZH_HG_001_HE160219_2016-05-19', 'ZH_HG_001_HG110167_2011-09-23', 'ZH_OG_001_KD150013_2016-01-05', 'ZH_OG_001_LA040062_2005-05-16', 'ZH_OG_001_LA150020_2016-03-17', 'ZH_OG_001_LA190001_2019-02-05', 'ZH_OG_001_LB000123_2004-01-13', 'ZH_OG_001_LB020005_2003-01-10', 'ZH_OG_001_LB030093_2004-05-25', 'ZH_OG_001_LB040004_2004-01-16', 'ZH_OG_001_LB040067_2005-01-28', 'ZH_OG_001_LB040072_2004-09-15', 'ZH_OG_001_LB060125_2007-02-20', 'ZH_OG_001_LB110028_2012-10-11', 'ZH_OG_001_LB120037_2012-08-23', 'ZH_OG_001_LB120077_2012-12-14', 'ZH_OG_001_LB120082_2013-03-08', 'ZH_OG_001_LB140010_2014-02-03', 'ZH_OG_001_LB180024_2018-08-23', 'ZH_OG_001_LB180047_2018-11-12', 'ZH_OG_001_LB200026_2020-08-12', 'ZH_OG_001_LC040043_2005-02-28', 'ZH_OG_001_LC110031_2012-12-06', 'ZH_OG_001_LC120044_2012-12-04', 'ZH_OG_001_LC120054_2012-12-10', 'ZH_OG_001_LC160032_2016-12-13', 'ZH_OG_001_LD160001_2016-04-18', 'ZH_OG_001_LE130071_2013-12-06', 'ZH_OG_001_LE140033_2014-06-23', 'ZH_OG_001_LE140055_2014-09-25', 'ZH_OG_001_LE180047_2018-08-22', 'ZH_OG_001_LF140015_2014-04-10', 'ZH_OG_001_LF140055_2014-07-18', 'ZH_OG_001_LM010006_2002-02-22', 'ZH_OG_001_LN030016_2003-05-07', 'ZH_OG_001_LN030022_2003-06-02', 'ZH_OG_001_LN030034_2003-05-09', 'ZH_OG_001_LN040023_2004-07-07', 'ZH_OG_001_LP020022_2002-09-02', 'ZH_OG_001_LP020055_2003-02-26', 'ZH_OG_001_LP040049_2004-05-17', 'ZH_OG_001_LP040057_2005-02-24', 'ZH_OG_001_LP040173_2005-03-17', 'ZH_OG_001_LP050024_2005-11-17', 'ZH_OG_001_LQ050062_2006-02-16', 'ZH_OG_001_LY110022_2011-08-24', 'ZH_OG_001_LY190021_2019-10-31', 'ZH_OG_001_LY190052_2020-01-10', 'ZH_OG_001_LZ190014_2019-08-26', 'ZH_OG_001_NA110008_2011-03-24', 'ZH_OG_001_NA120020_2012-06-27', 'ZH_OG_001_NC060009_2006-10-03', 'ZH_OG_001_NC150001_2015-12-09', 'ZH_OG_001_NC200002_2020-07-22', 'ZH_OG_001_NE020035_2002-10-22', 'ZH_OG_001_NE020044_2003-03-18', 'ZH_OG_001_NE030038_2004-01-06', 'ZH_OG_001_NE090030_2011-09-09', 'ZH_OG_001_NE110005_2011-03-09', 'ZH_OG_001_NF070008_2007-10-31', 'ZH_OG_001_NG060005_2007-01-24', 'ZH_OG_001_NG060018_2007-03-05', 'ZH_OG_001_NG070006_2007-01-18', 'ZH_OG_001_NG100003_2010-05-26', 'ZH_OG_001_NG130008_2013-08-22', 'ZH_OG_001_NG140002_2015-01-06', 'ZH_OG_001_NL050109_2005-12-30', 'ZH_OG_001_NN010047_2001-06-22', 'ZH_OG_001_NN030139_2004-10-27', 'ZH_OG_001_NN040093_2004-07-16', 'ZH_OG_001_NQ110017_2011-09-08', 'ZH_OG_001_NQ110033_2011-08-26', 'ZH_OG_001_NQ120050_2012-11-08', 'ZH_OG_001_NR040020_2004-02-23', 'ZH_OG_001_NR080032_2008-04-29', 'ZH_OG_001_NX000004_2000-05-12', 'ZH_OG_001_NX040009_2004-02-27', 'ZH_OG_001_NX040021_2004-07-07', 'ZH_OG_001_NX060045_2006-07-12', 'ZH_OG_001_NX060052_2006-07-27', 'ZH_OG_001_NX080012_2008-04-28', 'ZH_OG_001_NZ080005_2009-01-05', 'ZH_OG_001_PA140023_2014-07-09', 'ZH_OG_001_PC130059_2014-01-07', 'ZH_OG_001_PC130067_2014-06-02', 'ZH_OG_001_PC170010_2017-05-22', 'ZH_OG_001_PC180004_2018-03-02', 'ZH_OG_001_PC180018_2018-12-11', 'ZH_OG_001_PD200012_2020-10-15', 'ZH_OG_001_PF110056_2011-10-07', 'ZH_OG_001_PF110056_2011-10-11', 'ZH_OG_001_PF120017_2012-05-10', 'ZH_OG_001_PF130018_2013-06-13', 'ZH_OG_001_PF170053_2018-02-05', 'ZH_OG_001_PF170054_2017-12-20', 'ZH_OG_001_PF190060_2020-01-06', 'ZH_OG_001_PF200064_2020-07-15', 'ZH_OG_001_PN030117_2003-06-30', 'ZH_OG_001_PN040151_2004-07-27', 'ZH_OG_001_PN090194_2009-12-15', 'ZH_OG_001_PN100024_2010-03-03', 'ZH_OG_001_PP110019_2011-11-22', 'ZH_OG_001_PP130003_2013-02-21', 'ZH_OG_001_PP190038_2019-10-02', 'ZH_OG_001_PP200023_2020-08-11', 'ZH_OG_001_PQ130003_2013-03-11', 'ZH_OG_001_PQ140012_2014-04-24', 'ZH_OG_001_PQ140079_2014-12-12', 'ZH_OG_001_PQ150050_2015-09-03', 'ZH_OG_001_PQ160040_2016-06-21', 'ZH_OG_001_PQ200007_2020-05-08', 'ZH_OG_001_PQ200021_2020-05-19', 'ZH_OG_001_PS110012_2011-03-07', 'ZH_OG_001_PS110088_2011-05-19', 'ZH_OG_001_PS110112_2011-07-06', 'ZH_OG_001_PS110127_2011-08-02', 'ZH_OG_001_PS120026_2012-03-09', 'ZH_OG_001_PS120092_2012-05-22', 'ZH_OG_001_PS120123_2012-07-17', 'ZH_OG_001_PS120167_2012-09-28', 'ZH_OG_001_PS120221_2012-11-19', 'ZH_OG_001_PS130032_2013-03-14', 'ZH_OG_001_PS130054_2013-04-12', 'ZH_OG_001_PS130124_2013-08-07', 'ZH_OG_001_PS130162_2013-10-16', 'ZH_OG_001_PS130222_2014-04-11', 'ZH_OG_001_PS140075_2014-05-09', 'ZH_OG_001_PS140279_2015-01-07', 'ZH_OG_001_PS150089_2015-05-29', 'ZH_OG_001_PS150198_2015-12-09', 'ZH_OG_001_PS160042_2016-03-14', 'ZH_OG_001_PS170167_2017-08-03', 'ZH_OG_001_PS190136_2019-08-21', 'ZH_OG_001_RA120002_2012-05-31', 'ZH_OG_001_RB150016_2015-07-08', 'ZH_OG_001_RB150031_2015-11-16', 'ZH_OG_001_RB150039_2016-01-06', 'ZH_OG_001_RE130010_2013-04-17', 'ZH_OG_001_RE140024_2014-11-10', 'ZH_OG_001_RE170014_2018-03-20', 'ZH_OG_001_RT130017_2013-02-19', 'ZH_OG_001_RT130031_2013-02-21', 'ZH_OG_001_RT130087_2013-06-03', 'ZH_OG_001_RT130168_2013-10-15', 'ZH_OG_001_RT130173_2013-12-18', 'ZH_OG_001_RT140164_2014-12-01', 'ZH_OG_001_RT140165_2014-12-01', 'ZH_OG_001_RT140188_2015-01-08', 'ZH_OG_001_RT150159_2015-12-04', 'ZH_OG_001_RT160158_2016-10-03', 'ZH_OG_001_RT160209_2016-12-23', 'ZH_OG_001_RT170122_2017-08-24', 'ZH_OG_001_RT170162_2017-10-09', 'ZH_OG_001_RT170163_2017-10-09', 'ZH_OG_001_RT180015_2018-02-12', 'ZH_OG_001_RT180112_2018-07-05', 'ZH_OG_001_RT180139_2018-09-20', 'ZH_OG_001_RT180222_2019-02-11', 'ZH_OG_001_RT190027_2019-03-29', 'ZH_OG_001_RU120061_2012-10-16', 'ZH_OG_001_RU130069_2014-03-27', 'ZH_OG_001_RU180049_2018-11-16', 'ZH_OG_001_RU190016_2019-04-16', 'ZH_OG_001_RU190037_2019-07-12', 'ZH_OG_001_RU190055_2019-10-09', 'ZH_OG_001_RV130003_2013-05-17', 'ZH_OG_001_RV150010_2015-11-05', 'ZH_OG_001_RZ160007_2016-09-14', 'ZH_OG_002_SB040270_2004-09-07', 'ZH_OG_002_SB050100_2005-06-07', 'ZH_OG_002_SB050121_2005-10-13', 'ZH_OG_002_SB050136_2005-06-27', 'ZH_OG_002_SB050147_2005-05-25', 'ZH_OG_002_SB0503554_2005-11-16', 'ZH_OG_002_SB120160_2012-04-04', 'ZH_OG_002_SB150376_2015-10-06', 'ZH_OG_002_SB160135_2016-06-02', 'ZH_OG_002_SB160392_2017-06-02', 'ZH_OG_002_SB180144_2018-08-31', 'ZH_OG_002_SB180374_2018-09-11', 'ZH_OG_002_SB200439_2020-11-02', 'ZH_OG_002_SU120071_2013-05-08', 'ZH_OG_002_SU180018_2019-03-06', 'ZH_OG_002_UH140119_2014-07-24', 'ZH_OG_002_UN020092_2002-11-04', 'ZH_OG_004_PG140002_2014-09-03', 'ZH_OG_004_PG140002_2014-09-22', 'ZH_OG_004_VO120172_2012-11-30', 'ZH_OG_004_VO150035_2015-03-19', 'ZH_OG_004_VV110014_2011-07-07', 'ZH_OG_004_VV110017_2011-08-23', 'ZH_OG_005_KG050018_2005-11-03', 'ZH_OG_005_KG090015_2010-04-01', 'ZH_OG_006_2002-348-Z_2003-05-05', 'ZH_OG_006_AA050131_2005-11-10', 'ZH_OG_999_4A-39-2008_2008-04-03', 'ZH_OG_999_BX140002_2014-06-26', 'ZH_OG_999_BX140006_2014-11-25', 'ZH_OG_999_FV140173_2014-09-18', 'ZH_OG_999_MB120045-L-U_2014-02-20', 'ZH_OG_999_MM130346-L-U_2013-11-05', 'ZH_OG_999_VO110101_2011-09-08', 'ZH_OG_999_undefined_2011-03-04', 'ZH_SOBE_001_undefined_2004-07-16']
    for filename in sorted(os.listdir(PATH_TO_DATA)):
        if filename.endswith("pdf") and filename[:-4] in file_list and not filename.startswith("ZH_HG_001_HG130087_2015-01-29") and not filename.startswith("ZH_OG_002_SB110505_2012-04-03") and not filename.startswith("ZH_OG_002_SU120046_2012-10-26"):
            print(f"The following file is being processed:\n{os.path.join(PATH_TO_DATA, filename)}\n")
            # parse with tika library from separate script
            # parsed_text = tika_parse(os.path.join(PATH_TO_DATA, filename))
            # lines = split_lines(parsed_text)

            # parse with pdftotree library
            lines = parse_pdftotree(filename)

            pages = get_pages(lines)
            # # footnotes = get_footnotes(lines)
            if filename.startswith("ZH_BK") or filename.startswith("ZH_SOBE"):
                clean_text = get_paras(lines)
            else:
                clean_text = get_paras_hg(lines)

            # create new filenames for the xml files
            if filename.endswith("nodate.html"):
                xml_filename = filename.replace("nodate.html", "0000-00-00.xml")
            else:
                xml_filename = filename[:-4] + ".xml"

            # open json pendant
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
