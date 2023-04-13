#!/usr/bin/env python3
# -*- encoding: utf-8 -*-


# import necessary modules
import argparse
from tika import parser


parser = argparse.ArgumentParser(description="extract Text from PDF-files")
parser.add_argument("-p", "--path_to_data", type=str, help="path to the folder containing PDFs")
parser.add_argument("-s", "--save_folder", type=str, help="name of the folder where the text is to be saved")

args = parser.parse_args()

PATH_TO_DATA = "/home/admin1/tb_tool/scraping_data/"+args.path_to_file
SAVE_PATH = "/home/admin1/tb_tool/test_pdf_conversions/"+args.save_folder

# opening pdf file
def parse(filename):
    parsed_pdf = parser.from_file(filename)

# saving content of pdf
# you can also bring text only, by parsed_pdf['text']
# parsed_pdf['content'] returns string
#data = parsed_pdf['content']

# Printing of content
    print(data)

# <class 'str'>
#print(type(data))

# ['metadata'] attribute returns
# key-value pairs of meta-data
# print(parsed_pdf['metadata'])

# <class 'dict'>
# print(type(parsed_pdf['metadata']))

def main():
    filetype = "pdf"
    for filename in sorted(os.listdir(directory)):
        if filename.endswith(filetype):
            parse(filename)

if __name__ == "__main__":
    main()
