'''
yaml2csv.py
2 September 2025

YAML to CSV converter for Lewis Latin Lexicon file
'''
import yaml, csv

with open('lewis.yaml') as f:
    lewis_yaml = yaml.safe_load(f)

print(lewis_yaml.items())
# fieldnames = set()
# for key, values in lewis_yaml.items():
#     for entry in values: 
#         fieldnames.add(entry)
# print("Fieldnames:", fieldnames)