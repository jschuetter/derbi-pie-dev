'''
kaikki_importer.py

An importer script to automate the steps of creating a
DERBi PIE-friendly .csv from the Kaikki Wiktextract data.

N.B. each language might have some nuance that needs to be
handled manually - e.g. Kaikki doesn't provide a 'transliteration'
field, so `lemma_translit` would need to be filled in manually
using another library when appropriate.

All files are written in the `/kaikki-output/` local directory
'''

import jsonlparser
from jsonlparser import parse_jsonl
from jsonlreader import *
from ..helpers.renum_main import renumber_main

import os, re
from time import time

OUTPUT_DIR = "kaikki-output/"

# Get language information
lang_name = input("What is the name of the lanugage you are trying to parse?\n")
wiki_lang_name = input("\nWhat is the name of the language in the Wiktextract data? (leave blank if same)\n") or lang_name
lang_path_safe = lang_name.replace(" ", "_")
if not re.fullmatch(r'[a-zA-Z_\-]+', lang_path_safe):
    raise ValueError(f"Language name '{lang_path_safe}' is not path-safe. Please enter a different name")
lang_code = input("\nWhat is the DERBi PIE language code for this language?\n")
if lang_name == "" or lang_code == "":
    raise ValueError("Please provide non-empty values for both the language name and DERBi PIE code.")

# Create language directory, if necessary
lang_dir = os.path.join(OUTPUT_DIR, lang_path_safe)
if not os.path.exists(lang_dir):
    os.makedirs(lang_dir, exist_ok=True)
    print("Created directory", lang_dir)
else: 
    print("Directory", lang_dir, "exists.")

# Extract data from enwiktionary dump
print("Extracting relevant data from enwiktionary dump...")
jsonl_path = os.path.join(lang_dir, f"{lang_path_safe}.jsonl")
extract_start = time()
parse_jsonl(input_file=jsonlparser.RAW_FILE, output_file=jsonl_path, lang=wiki_lang_name)
print("Data extract completed. Runtime:", time() - extract_start, "s")

# Parse JSONL data
print("Parsing JSONL into DERBi PIE format")
# Normalize language class name
lang_html = re.sub(r'[^a-z]', '', lang_name.lower())
csv_path = os.path.join(lang_dir, f"{lang_path_safe}.csv")
parse_start = time()
entries = get_entries(jsonl_path, lang=lang_html, lang_code=lang_code)
save_csv(entries, csv_path)
print(f"Parsing completed.")

# Renumber main entries to align with convention
# See header comment in ~/lexicon/helpers/renum_main.py
print("Renumbering main entries")
renumber_main(csv_path)
print(f"Processing completed. See output in {lang_dir}.")
print("Runtime:", time() - parse_start, "s")
print("Total runtime:", time() - extract_start, "s")