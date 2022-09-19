# -*- encoding: utf-8 -*-

# use following CLI command:
# python3.10 sh_og_scraper.py -p SH_OG -s SH_OG_clean

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


absatz_pattern = r"^((\d{1,2}\.\–)?((\s{1,2})?[a-k]+\))+|\d{1,2}\.\–)\s"
absatz_pattern2 = r"^((\d{1,2}\.\–)?((\s{1,2})?[a-k]+\))+|\d{1,2}\.\–)\s"
absatz_pattern3 = r"^((\d{1,2}\.\–)?((\s{1,2})?[a-k]+\))+|\d{1,2}\.\–)\s"
# absatz_pattern2 = r"^[0-9]{1,2}\.(\/)?([0-9]{1,2}(\.)?)*\s"
# absatz_pattern3 = r"^((\s)?[A-Z]\.(\/)?((\s)?[a-z])*|[IVD]{1,4}\.)\s"
datum_pattern = r"[0-9][0-9]?\.(\s?(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)|([0-9]{2}\.))"
false_marks = []


def split_lines(parsed_text: str) -> List[str]:
    split_lines = [line.strip().replace("     ", " ").replace("\uf02d", "").replace(" ", "").replace("\xa0\xa0\xa0\xa0\xa0\xa0", "").replace("\xa0", "") for line in parsed_text.split("\n")]
    return split_lines


def get_pages(lines: List[str]) -> str | None:
    pages = [lines.pop(lines.index(line)) for i, line in enumerate(lines)
             if line.isdigit()
             and re.fullmatch(r"\d{4}", lines[i-2])]
    if pages:
        if pages[0] == "2": pages[0] = "1"
        return f"{pages[0]}–{pages[-1]}"
    else:
        return ""


def get_footnotes(lines: List[str]) -> dict[str: str]:
    footnotes = {}
    last_num = 0
    fn_pattern = r"\d{1,2}\s{2}[A-Z].*$"
    for i, line in enumerate(lines):
        text = []
        line = line.strip()
        end_num = 0
        if re.fullmatch(fn_pattern, line):
            match = re.fullmatch(fn_pattern, line).group(0)
            fn_num, text = match.split("  ")[0], [match.split("  ")[1].strip()]
            if not text[0].endswith("."):
                for j in range(1, 10):
                    if len(lines) >= i+j+1 and lines[i+j]:
                        text.append(lines[i+j].rstrip("-"))
                    if len(lines) >= i+j+1 and lines[i+j].endswith("."):
                        end_num = j
                        break
                fn_text = " ".join(text)
            else:
                fn_text = text[0]
        elif line.isdigit() and lines[i+2] and not lines[i+2].strip()[0] in r"[A-Z]":
            fn_num, text = line, [lines[i+2].strip()]
            if not text[0].endswith("."):
                for j in range(1, 10):
                    if len(lines) >= i+j+1 and lines[i+j]:
                        text.append(lines[i+j].rstrip("-"))
                    if len(lines) >= i+j+1 and lines[i+j].endswith("."):
                        end_num = j
                        break
                fn_text = "".join(text)
            else:
                fn_text = text[0]
        else:
            if not footnotes and line == "1":
                fn_num = line
                for j in range(1, 10):
                    if len(lines) >= i+j+1 and lines[i + j]:
                        text.append(lines[i + j].rstrip("-"))
                    if len(lines) >= i+j+1 and lines[i + j].endswith("."):
                        end_num = j
                        break
                fn_text = " ".join(text)
            elif footnotes and line.isdigit():
                fn_num = line
                for j in range(1, 10):
                    if len(lines) >= i+j+1 and lines[i + j]:
                        text.append(lines[i + j].rstrip("-"))
                    if lines[i + j].endswith("."):
                        end_num = j
                        break
                fn_text = "".join(text)
            else:
                continue
        if int(fn_num) - 1 == last_num and fn_text and fn_text[0].isupper() and fn_text.endswith("."):
            footnotes[fn_num] = fn_text
            last_num = int(fn_num)
            lines[i] = ""
            if end_num:
                for k in range(1, end_num):
                    lines[i+k] = ""
    # for i, line in enumerate(lines):
    #     text = []
    #     line = line.strip()
    #     end_num = 0
    #     if (line.isdigit() and not re.fullmatch(r"\d{4}", line) and not lines[i-1])\
    #             or re.fullmatch(fn_pattern, line):
    #         if re.fullmatch(fn_pattern, line):
    #             match = re.fullmatch(fn_pattern, line).group(0)
    #             fn_num, text = match.split("  ")[0], [match.split("  ")[1].strip()]
    #             if not text[0].endswith("."):
    #                 for j in range(1, 10):
    #                     if lines[i+j]:
    #                         text.append(lines[i+j].rstrip("-"))
    #                     if lines[i+j].endswith("."):
    #                         end_num = j
    #                         break
    #                 fn_text = " ".join(text)
    #             else:
    #                 fn_text = text[0]
    #         else:
    #             if not footnotes and line == "1":
    #                 fn_num = line
    #                 for j in range(1, 10):
    #                     if lines[i + j]:
    #                         text.append(lines[i + j].rstrip("-"))
    #                     if lines[i + j].endswith("."):
    #                         end_num = j
    #                         break
    #                 fn_text = " ".join(text)
    #             elif footnotes and line.isdigit():
    #                 fn_num = line
    #                 for j in range(1, 10):
    #                     if lines[i + j]:
    #                         text.append(lines[i + j].rstrip("-"))
    #                     if lines[i + j].endswith("."):
    #                         end_num = j
    #                         break
    #                 fn_text = " ".join(text)
    #             else:
    #                 continue
    #         if int(fn_num) - 1 == last_num and fn_text[0].isupper() and fn_text.endswith("."):
    #             footnotes[fn_num] = fn_text
    #             last_num = int(fn_num)
    #             lines[i] = ""
    #             if end_num:
    #                 for k in range(1, end_num):
    #                     lines[i+k] = ""

    return footnotes


def get_paras(lines: List[str]) -> List[str]:
    clean_lines = []
    para = ""
    pm_counter = 0
    erw_counter = 0
    headnote_counter = 0

    for i, line in enumerate(lines):
        line = line.strip()

        # remove all headnotes but the first
        if re.fullmatch(r"\d{4}", line):
            headnote_counter += 1
            if headnote_counter > 1:
                continue

        # # get start of main text
        # if  ("in Anbetracht dessen" in line or "Sachverhalt" in line or "hat das Verwaltungsgericht festgestellt" in line  or "Aus den Erwägungen" in line or "Entscheid Kantonsgericht" in line or "Entscheid Handelsgericht" in line or "Entscheid Anklagekammer" in line) and not line.endswith("Publikationsplattform"):
        #     clean_lines.append(line.strip())
        #     sachverhalt_counter += 1
        #     continue
        #
        # if sachverhalt_counter == 0 and line:
        #     clean_lines.append(line.strip())
        #
        # else:

        # # get footnote reference in text
        # if re.match(r"^.*\.\d{1,2}$", line):
        #     if para:
        #         clean_lines.append(para.strip())
        #         para = ""
        #     clean_lines.append(line)
        #
        # elif line.isdigit() and lines[i - 1] and not re.fullmatch(r"\d{4}", line):
        #
        if "Aus den Erwägungen" in line and not erw_counter:
            if para:
                clean_lines.append(para.strip())
                para = ""
            clean_lines.append(line)
            erw_counter += 1
            continue

        # match pure paragraph numbers
        elif (re.fullmatch(absatz_pattern[:-2], line) or re.fullmatch(absatz_pattern2[:-2], line) or re.fullmatch(absatz_pattern3[:-2], line)) and not re.fullmatch(datum_pattern, line) and not re.match("^\w\._+", line):
            if para:
                clean_lines.append(para.strip())
                para = ""
            clean_lines.append(line)
            pm_counter += 1

        # match paragraph numbers with additional text and split
        elif (re.match(absatz_pattern, line) or re.match(absatz_pattern2, line) or re.match(absatz_pattern3, line)) and not re.match(datum_pattern, line) and not line.endswith("Kammer"):
            if re.match(absatz_pattern, line): match = re.match(absatz_pattern, line).group(0)
            if re.match(absatz_pattern2, line): match = re.match(absatz_pattern2, line).group(0)
            if re.match(absatz_pattern3, line): match = re.match(absatz_pattern3, line).group(0)
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
    # fn_ref_pattern = r"([.);]|[.);]\s)(\d{1,2}|[A-Z]{2}\d{1,2}\.\))(\s[A-Z])"
    # fn_ref_pattern = r"([A-Za-z]\s|-|%|\)\s|\.)(\d{1,2})(\s[A-Za-z]|\s\.|\s\))"
    # fn_ref_end_pattern = r"([.);]|\.\s)(\d{1,2})$"
    fn_false_pattern = r"(Abs\.\s|Art\.\s)(\d{1,2})(\s)?"
    footnotes_copy = footnotes.copy()

    for para in filter_list:
        p_node = ET.SubElement(body_node, "p")
        match_indeces = []
        if footnotes:
            fn_counter = 0
            it = 1
            for i in range(it, len(footnotes) + 1):
                fn_ref_pattern = fr"([.);]|[.);]\s|[A-Z][A-Z]\s)({i})(\s[A-Z]|\s\))"
                fn_ref_end_pattern = fr"([.);]|\.\s)({i})$"
                if re.search(fn_ref_pattern, para) or re.search(fn_ref_end_pattern, para):
                    matches = re.findall(fn_ref_pattern, para) or re.findall(fn_ref_end_pattern, para)
                    for match in matches:
                        if len(match) == 3 and match[1] in footnotes_copy:
                            para = re.sub(f"([.);]|[.);]\s|[A-Z][A-Z]){match[1]}(\s[A-Z])", f"{match[0]}[[{match[1]}]]{match[2]}", para)
                            del footnotes_copy[match[1]]
                            # print(match[1])
                            it+=1
                        elif len(match) == 2 and match[1] in footnotes_copy:
                            para = re.sub(f"([.);]|\.\s){match[1]}$", f"{match[0]}[[{match[1]}]]",
                                          para)
                            # print(match[1])
                            del footnotes_copy[match[1]]
                            it+=1
                p_node.attrib["type"] = "plain_text"
            # if (re.search(fn_ref_pattern, para) or re.search(fn_ref_end_pattern, para)):
            #     if re.search(fn_ref_end_pattern, para):
            #         matches = re.findall(fn_ref_end_pattern, para)
            #     else:
            #         matches = re.findall(fn_ref_pattern, para)
            #     for match in matches:
            #         if match[1] in footnotes_copy and not re.match(fn_false_pattern, "".join(match)):
            #             if re.search(fn_ref_end_pattern, para):
            #                 para = re.sub(fr"(\.\s?){match[1]}$",
            #                               f"{match[0]}[[{match[1]}]]",
            #                               para)
            #             else:
            #                 para = re.sub(fr"([A-Za-z]\s|-|%|\)\s|\.){match[1]}(\s[A-Za-z]|\s\.|\s\))",
            #                               f"{match[0]}[[{match[1]}]]{match[2]}",
            #                               para)
            #
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
    for fn_mark in footnotes:
        p_node = ET.SubElement(body_footnote_node, "p")
        p_node.attrib["type"] = "footnote"
        p_node.text = f"{fn_mark} {footnotes[fn_mark]}"
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
    f_names = ["SH_OG_001_93-2013-22_2014-12-30.pdf", "SH_OG_001_Nr-96-2014-3_2014-10-21.pdf", "SH_OG_001_10-1998-28_2001-07-06.pdf"]
    for filename in sorted(os.listdir(PATH_TO_DATA)):
        if filename.endswith("pdf"): # and filename in f_names:
            print(f"The following file is being processed:\n{os.path.join(PATH_TO_DATA, filename)}\n")

            # parse with tika library from separate script
            parsed_text = tika_parse(os.path.join(PATH_TO_DATA, filename))

            # parse with pdftotree library
            # lines = parse_pdftotree(filename)

            lines = split_lines(parsed_text)
            pages = get_pages(lines)
            footnotes = get_footnotes(lines)
            clean_text = get_paras(lines)
            #
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
                    tree = build_xml_tree(filename, loaded_json, clean_text, pages=pages, footnotes=footnotes)  # generates XML tree
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
