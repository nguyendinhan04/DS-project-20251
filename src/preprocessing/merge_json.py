import json
import os
import pandas as pd



path = "../data/crawled"
merged_file_path = "../data/merged/merged.jsonl"


# make merged file empty
open(merged_file_path, 'w').close()

# list all , folder in path
# print pwd
print("Current working directory:", os.getcwd())
folders = [f.path for f in os.scandir(path) if f.is_dir()]
for folder in folders:
    # loop through all json files in folder
    merged_data = []
    region_name = folder.split('\\')[-1]
    json_files = [f for f in os.listdir(folder) if f.endswith('.json')]
    for json_file in json_files:
        print("Processing file:", json_file)
        with open(os.path.join(folder, json_file), 'r', encoding='utf-8') as f:
            data = json.load(f)
            for entry in data:
                entry['region'] = region_name
            merged_data.extend(data)
    # write merged data to new json file with json line format
    with open(merged_file_path, 'a', encoding='utf-8') as f:
        for entry in merged_data:
            f.write(json.dumps(entry) + '\n')
    print(f"Merged {len(json_files)} files into {merged_file_path}, total entries: {len(merged_data)}")
    # break # only process the first folder for now
