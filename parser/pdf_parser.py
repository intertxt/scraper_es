# -*- encoding: utf-8 -*-

# import necessary modules
import argparse
import os
from tika import parser
import pdftotree
import xml.etree.ElementTree as ET


arg_parser = argparse.ArgumentParser(description="extract Text from PDF-files")
arg_parser.add_argument("-p", "--path_to_data", type=str, help="path to the folder containing PDFs")
arg_parser.add_argument("-s", "--save_folder", type=str, help="name of the folder where the text is to be saved")

args = arg_parser.parse_args()


# PATH_TO_DATA = "/home/admin1/tb_tool/scraping_data/"
# SAVE_PATH = "/home/admin1/tb_tool/test_pdf_conversions/"+args.save_folder


def tika_parse(filename):
    """Converting a PDF file to text with Tika. Java has to be installed and accessible for this."""
    parsed_pdf = parser.from_file(filename)

# saving content of pdf
# you can also bring text only, by parsed_pdf['text']
# parsed_pdf['content'] returns string
    return parsed_pdf['content']


def main():
    filetype = "pdf"
    for folder in sorted(os.listdir(PATH_TO_DATA)):
        for filename in sorted(os.listdir(PATH_TO_DATA+"/"+folder))[:2]:
            if filename.endswith(filetype):
                print(f"The following file is being processed:\n{os.path.join(PATH_TO_DATA, folder, filename)}\n")
                print(f"TIKA:")
                parsed_text = tika_parse(os.path.join(PATH_TO_DATA, folder, filename))
                print(parsed_text)
                # print("----------------------------------------------------------\n")
                # Converting a PDF file to text with pdftotree.
                # print("XML Elements:\n")
                # xml_tree_string = pdftotree.parse(os.path.join(PATH_TO_DATA, folder, filename))
                # xml_tree = ET.fromstring(xml_tree_string)
                # get a listing of all elements with a "class" attribute
                # xml_element_list = list(set([f"{element.tag}: {element.attrib['class']}" for element in xml_tree.iter() if element.tag in ["div", "span"]]))
                # for element in xml_element_list:
                #     print(element)
                # print("\n")
                # print("PDFTOTREE:\n")
                # ET.dump(xml_tree)
                print("===========================================================\n\n")


if __name__ == "__main__":
    main()
