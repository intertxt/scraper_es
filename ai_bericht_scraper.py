# -*- encoding: utf-8 -*-

# use following CLI command:
# python3.10 ai_bericht_scraper.py -p AI_Bericht -s AI_Bericht_clean

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
absatz_pattern3 = r"^((\s)?[A-D]\.(\/)?((\s)?[a-z])*|[IVD]{1,4}\.)\s"
datum_pattern = r"[0-9][0-9]?\.(\s?(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)|([0-9]{2}\.))"
false_marks = []

def split_lines(parsed_text: str) -> List[str]:
    split_lines = [line.strip().replace("     ", " ").replace("\uf02d", "").replace(" ", "").replace("\uf0a7 ", "").replace("\xa0", "") for line in parsed_text.split("\n")]
    return split_lines


def get_content_list(lines: List[str]) -> List[Tuple[str, str, str]]:
    """Extracts the content list into the following structure List[Tuple[number, title, page]] if the tuples are of
    smaller size than 3, they might be titles or appendices."""
    start_index = [lines.index(line) for line in lines if re.match(r"Verwaltungs\-\sund\sGerichtsentscheide\s+1", line)][0] -1
    end_index = [lines.index(line) for line in lines if re.match(r"\d\.\s+Gerichte\s+\d{1,3}", line)][0] + 1
    content_list = [lines.pop(lines.index(line)).split() for line in lines[start_index:end_index]]
    pretty_content_list = []
    for line in content_list:
        if line:
            if line[0] == 'Verwaltungs-':
                pretty_content_list.append((" ".join(line[0:3]), line[3]))
            else:
                pretty_content_list.append(tuple(line))


    return pretty_content_list


def get_content_list_gb(lines: List[str]) -> List[Tuple[str, str, str]]:
    """Extracts the content list into the following structure List[Tuple[number, title, page]] if the tuples are of
    smaller size than 3, they might be titles or appendices."""
    content_pages = [line for line in lines if re.fullmatch(r"[IVX]{1,3}\s-\s[IVX]{1,3}", line)]
    start_index = [lines.index(line) for line in lines if re.match(r"^Inhaltsverzeichnis$", line)][0] - 1
    end_index = [lines.index(line) for line in lines if re.match(r"^\d{1,3}\s-\s\d{1,3}(\sAI\s.*)?$", line)][0] - 1
    content_list = [lines.pop(lines.index(line)).split(".") for line in lines[start_index:end_index]]
    content_list = list(filter(lambda x: x != [], content_list))
    clean_content = []
    for line in content_list:
        if line and not re.fullmatch(r"[IVX]{1,3}\s-\s[IVX]{1,3}", line[0]) and not re.match(r"^Geschäftsbericht\s\d{4}$", line[0]):
            clean_elem = []
            for elem in line:
                if elem:
                    clean_elem.append(elem.strip())
            if clean_elem:
                clean_content.append(clean_elem)

    pretty_content_list = []
    for line in clean_content:
        if line:
            if line[0] == 'Inhaltsverzeichnis':
                pretty_content_list.append(line[0])
            elif len(line) == 2:
                tup = (line[0].split(" ", 1).append(line[1]))
                if tup:
                    tup = tuple(filter(lambda x: x != "", tup))
                    pretty_content_list.append(tup)
            else:
                pretty_content_list.append(tuple(line))
    pretty_content_list = list(filter(lambda x: x != None, pretty_content_list))

    return pretty_content_list


def get_pages(lines: List[str]) -> str | None:
    pages = [lines.pop(lines.index(line)) for line in lines if line.isdigit() and len(line)<4]
    if pages:
        if pages[0] == "2": pages[0] = "1"
        return f"{pages[0]}–{pages[-1]}"
    else:
        return ""


def get_pages_gb(lines: List[str]) -> str | None:
    page_pattern = r"^\d{1,3}\s-\s\d{1,3}(\sAI\s.*)?$"
    content_pages = [lines.pop(lines.index(line)) for line in lines if re.fullmatch(r"[IVX]{1,3}\s-\s[IVX]{1,3}", line)]
    pages = [lines.pop(lines.index(line)).split()[0] for line in lines if re.fullmatch(page_pattern, line)]
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
    sachverhalt_counter = 1
    headnote_counter = 0
    headnote_pattern = r"^Geschäftsbericht\s\d{4}$"

    for i, line in enumerate(lines):
        line = line.strip()

        # # get start of main text
        # if  ("nachdem sich ergeben" in line or "Sachverhalt" in line):
        #     clean_lines.append(line.strip())
        #     sachverhalt_counter += 1
        #     continue

        # extract headnotes all but the first
        if re.fullmatch(headnote_pattern, line) and headnote_counter == 0:
            clean_lines.append(line.strip())
            headnote_counter += 1
        elif re.fullmatch(headnote_pattern, line):
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
            elif (re.match(absatz_pattern, line) or re.match(absatz_pattern2, line) or re.match(absatz_pattern3, line)) and not re.match(datum_pattern, line): 
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


def build_xml_tree(filename: str, loaded_json, filter_list: List, footnotes=None, pages=None, content_list=None):
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
    if content_list:
        body_content_list_node = ET.SubElement(text_node, "content_list")
        for line in content_list:
            node = ET.SubElement(body_content_list_node, "p")
            if line[0][0].isdigit(): node.attrib["num"] = line[0]
            if line[-1].isdigit(): node.attrib["page"] = line[-1]
            for l in line:
                if l and l[0].isalpha(): node.text = l
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
    for filename in sorted(os.listdir(PATH_TO_DATA))[40:]:
        if filename.endswith("pdf"):
            print(f"The following file is being processed:\n{os.path.join(PATH_TO_DATA, filename)}\n")

            # parse with tika library from separate script
            parsed_text = tika_parse(os.path.join(PATH_TO_DATA, filename))

            # parse with pdftotree library
            # lines = parse_pdftotree(filename)

            lines = split_lines(parsed_text)

            # files starting from 2004 have a different layout
            if int(filename[-8:-4]) >= 2004:
                if "Geschäftsbericht" in parsed_text and "Inhaltsverzeichnis" in parsed_text:
                    content_list = get_content_list_gb(lines)
                    pages = get_pages_gb(lines)
                else:
                    content_list = get_content_list(lines)
                    pages = get_pages(lines)
            else:
                pages = None
                content_list = None

            # footnotes = get_footnotes(lines)
            clean_text = get_paras(lines)

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
                    tree = build_xml_tree(filename, loaded_json, clean_text, pages=pages, content_list=content_list)  # generates XML tree
                    tree.write(os.path.join(SAVE_PATH, xml_filename), encoding="UTF-8", xml_declaration=True)  # writes tree to file
                    ET.dump(tree)  # shows tree in console

            # print(parsed_text)
            # print(lines)
            # print(pages)
            # for _ in footnotes:
            #     print(f"{_}\t{footnotes[_]}")
            # print(footnotes)
            # print(clean_text)
            # for _ in content_list:
            #     print(_)
            # print(content_list)



            print("\n===========================================================\n\n")


if __name__ == "__main__":
    main()
