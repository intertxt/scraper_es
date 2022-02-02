import os
import argparse
import operator


parser = argparse.ArgumentParser(description='generate clean XML-files from HTML-files')
parser.add_argument('-p','--path_to_data',type=str,help="directory where all the different data is stored")
parser.add_argument('-d','--directory',type=str,default='BS_Omni',help='current directory for the scraper')
parser.add_argument('-t','--type',type=str, default=".html", help="default filetype (html or pdf usually)")

args = parser.parse_args()

PATH_TO_DATA = args.path_to_data


def get_duplicates(directory):
    # gets a list of all actual duplicates
    meta_dict = {}
    duplicate_list = []
    for file in sorted(os.listdir(directory)):
        # if "nodate" in file:
        filename_split = file.rsplit("_", 1)
        # print(filename_split)
        if filename_split[0] not in meta_dict:
            meta_dict[filename_split[0]] = [{"fullname": file, "size": os.path.getsize(directory+"/"+file)}]
        else:
            meta_dict[filename_split[0]].append({"fullname": file, "size": os.path.getsize(directory+"/"+file)})

    for k, v in meta_dict.items():
        if len(v) > 2:
            v = sorted(v, key=operator.itemgetter('size'), reverse=True)
            i = 0
            current_size = v[i]["size"]
            for j, item in enumerate(v[i + 1:]):
                if item["size"] == current_size:
                    duplicate_list.append(v[j+1]["fullname"])
            else:
                i += 1
    return duplicate_list, len(duplicate_list)

def check_pendants(directory):
    # gets a list of files which do not have a json pendant
    file_dict = {}
    pendantless_files = []
    for file in sorted(os.listdir(directory)):
        file = file[:-5]
        if file in file_dict:
            file_dict[file] += 1
        else:
            file_dict[file] = 1
    for k, v in file_dict.items():
        if v == 1:
            pendantless_files.append(k)
    return pendantless_files, len(pendantless_files)

    """
    import os

meta_dict = {}

for file in directory:
    filename_split = file.rsplit("_")
    if filename_split not in meta_dict:
        meta_dict[filename_split] = [{"fullname":file,"size": os.path.getsize(file)}]
    else:
        meta_dict[filename_split].append({"fullname":file,"size": os.path.getsize(file)})

for k,v in meta_dict.items():
    if len(v) > 4: 
        v = sorted(v, key=itemgetter('size'))
        i = 0

        current_size = v[i]["size"]
        for j,item in enumerate(v[i+1:]):

            if item["size"] == current_size:
                print(v[i]["filename"] and v[j]["filename"] are duplicates)

            else:
                i += 1

    """


def main():
    print(get_duplicates(PATH_TO_DATA+args.directory))
    # print(check_pendants(PATH_TO_DATA+args.directory))

if __name__ == '__main__':
	main()