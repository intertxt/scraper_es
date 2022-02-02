import os
import argparse
import xml.etree.ElementTree as ET
import re


parser = argparse.ArgumentParser(description='extract_dates')
parser.add_argument('-d','--directory',type=str,help='current directory for the scraper as path')

args = parser.parse_args()

MONTH_DICT = {"Januar": "01",
              "Februar": "02",
              "März": "03",
              "April": "04",
              "Mai": "05",
              "Juni": "06",
              "Juli": "07",
              "August": "08",
              "September": "09",
              "Oktober": "10",
              "November": "11",
              "Dezember": "12",
              }

def main():
    directory =  args.directory
    # for subdirectory in os.walk(directory):
    for filename in sorted(os.listdir(directory)): # change to subdirectory
        # print(directory)
        if "0000-00-00.xml" in filename: # and filename == "CH_BGE_001_BGE-121-I-267_0000-00-00.xml":
        # if filename == "CH_BGE_001_BGE-121-I-245_1995-07-05.xml":
            tree = ET.parse(directory + filename)
            root = tree.getroot()
            if "0000-00-00" in root.attrib["date"] or not root.attrib["date"]:
                counter = 0
                for child in root[0][0:10]:
                    match = re.search(r"vom\s\d{1,2}\.\s(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s\d{4}", child.text)
                    if match:
                        match = match.group(0)[4:]
                        for k, v in MONTH_DICT.items():
                            if k in match:
                                if match[1]==".":
                                    date_for_header = match[-4:] + "-" + v + "-" + "0"+match[0]
                                else:
                                    date_for_header = match[-4:]+"-"+v+"-"+match[:2]
                        # prints date with text section where it was extracted from
                        print(f"{date_for_header}:\t\t{child.text}\n")
                        counter += 1
                if counter == 1:
                    new_filename = filename[:-14]+date_for_header+".xml"
                    print(f"The following file will be changed:\n"
                          f"{filename}\n"
                          f"into:\n"
                          f"{new_filename}\n\n"
                          f"Updated header:")
                    root.set("date", date_for_header)
                    root.set("decade", date_for_header[:3]+"0")
                    root.set("year", date_for_header[:4])
                    # ET.dump(tree)
                    # prints resulting header
                    # print(root.attrib)
                    # write new tree
                    tree.write(directory+new_filename, encoding="UTF-8", xml_declaration=True)
                    ET.dump(tree)
                    # remove old file
                    os.remove(directory+filename)
                    print("\n\n")

                else:
                    # in case there were more than one dates given in the file or none at all 
                    # no date is extracted
                    print(f'The date extraction was inconclusive for the following file: {filename}\n\n')





if __name__ == '__main__':
    main()