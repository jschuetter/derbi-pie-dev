'''
yaml2csv.py
2 September 2025

YAML to CSV converter for Lewis Latin Lexicon file
'''
# import xml, csv
import xml.etree.ElementTree as ET
import pandas as pd

tree = ET.parse("lewis.xml")
root = tree.getroot()
for child in root:
    print(child.tag, child.attrib, child.text)