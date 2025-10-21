'''
cltk-lemmatize.py
21 October 2025

Script for lemmatizing unmatched reflexes from lex_ref_link.
See `null_reflexes.csv` for input example
'''

import cltk
from cltk import NLP
from cltk.phonology import syllabifier_processes, transcription_processes
from cltk.dependency.tree import DependencyTree

from time import time
import csv, os, re

INPUT_FILE = "../MySQL/null_reflexes.csv"
OUTPUT_FILE = "../MySQL/null_reflexes_matched.csv"

# Read document
with open(INPUT_FILE) as text:
	full_text = text.read()

# Load pipeline for Latin
cltk_nlp = NLP(language="lat")
# Default: 
	# 'cltk.alphabet.processes.LatinNormalizeProcess'
	# 'cltk.dependency.processes.LatinStanzaProcess'
	# 'cltk.embeddings.processes.LatinEmbeddingsProcess'
	# 'cltk.stops.processes.StopsProcess'
	# 'cltk.lexicon.processes.LatinLexiconProcess'

# Customize pipeline
cltk_nlp.pipeline.processes.remove(cltk.embeddings.processes.LatinEmbeddingsProcess)
cltk_nlp.pipeline.processes.remove(cltk.stops.processes.StopsProcess)
cltk_nlp.pipeline.processes.remove(cltk.lexicon.processes.LatinLexiconProcess)
print(cltk_nlp.pipeline.processes)

# Analyze text
start_time = time()
cltk_doc = cltk_nlp.analyze(text=full_text)
print(f"Parsing time: {time() - start_time} seconds")

# Write Word data to CSV
word_start = time()
COLUMN_HEADERS = [
	"string",
	"lemma",
]
rows = []
sqlNull = "\\N"
for w in cltk_doc.words:
	row = {}
	for key in COLUMN_HEADERS:
		val = getattr(w, key)
		if (
			isinstance(val, cltk.morphology.morphosyntax.MorphosyntacticFeatureBundle) and len(val) == 0 or 
			val in ["{}", "[]", ""]
		):
			row[key] = sqlNull
		else: 
			row[key] = val
	rows.append(row)

# Create files if not existent
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
with open(OUTPUT_FILE, "w", newline='') as f:
	writer = csv.DictWriter(f, fieldnames=COLUMN_HEADERS)
	writer.writeheader()  # Write header row
	writer.writerows(rows)  # Write data rows
print(f"CSV write time: {time() - word_start} seconds")
print(f"Total runtime: {time() - start_time} seconds")