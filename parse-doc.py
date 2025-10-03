'''
parse-doc.py
03 October 2025

Document parsing script - version 2.
'''

import cltk
from cltk import NLP
from cltk.phonology import syllabifier_processes, transcription_processes
from cltk.dependency.tree import DependencyTree

from time import time
import csv, os, re

INPUT_FILE = "corpus/latin/livy.ab_urbe_condita.part.1.books_1-10.tess"
OUTPUT_DIR = "corpus/parsed/livy/ab_urbe_condita/"
OUTPUT_FILE = OUTPUT_DIR + "livy.ab_urbe_condita.part.1.csv"

# Read document
with open(INPUT_FILE) as text:
	full_text = text.read()
	# Remove the section in angle brackets at the beginning of each line
	clean_text = re.sub(r'^\<[ a-zA-Z0-9.]*\>\s', '', full_text, flags=re.MULTILINE)
	# Test text
	print(clean_text[:500])
	# Cut down document length for demo
	print("Approximate token count:", len(clean_text.split()))

# Load pipeline for Latin
cltk_nlp = NLP(language="lat")
# Default: 
	# 'cltk.alphabet.processes.LatinNormalizeProcess'
	# 'cltk.dependency.processes.LatinStanzaProcess'
	# 'cltk.embeddings.processes.LatinEmbeddingsProcess'
	# 'cltk.stops.processes.StopsProcess'
	# 'cltk.lexicon.processes.LatinLexiconProcess'

# Customize pipeline
# Pop embeddings process
cltk_nlp.pipeline.processes.remove(cltk.embeddings.processes.LatinEmbeddingsProcess)
# Remove lexicon process (separate lookup table)
cltk_nlp.pipeline.processes.remove(cltk.lexicon.processes.LatinLexiconProcess)
print(cltk_nlp.pipeline.processes)
print()
# Add other processes
# cltk_nlp.pipeline.processes.append(cltk.ner.processes.LatinNERProcess)  # NER unavailable for Latin?
cltk_nlp.pipeline.processes.append(syllabifier_processes.LatinSyllabificationProcess)
cltk_nlp.pipeline.processes.append(transcription_processes.LatinPhonologicalTranscriberProcess)
cltk_nlp.pipeline.processes.append(cltk.stem.processes.LatinStemmingProcess)
print("Final pipeline:", cltk_nlp.pipeline.processes)

# Analyze text
start_time = time()
cltk_doc = cltk_nlp.analyze(text=clean_text)
print(f"Parsing time: {time() - start_time} seconds")
print("Tokens parsed:", len(cltk_doc.words))
print("Sentences parsed:", len(cltk_doc.sentences_tokens))

# Write Word data to CSV
word_start = time()
COLUMN_HEADERS = [
	"index_token",
	"index_sentence",
	"string",
	"pos",
	"lemma",
	"stem",
	"dependency_relation",
	"governor",
	"features",
	"category",
	"syllables",
	"phonetic_transcription"
]
rows = [{key: getattr(w, key) for key in COLUMN_HEADERS} for w in cltk_doc.words]

# Create files if not existent
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
with open(OUTPUT_FILE, "w", newline='') as f:
	writer = csv.DictWriter(f, fieldnames=COLUMN_HEADERS)
	writer.writeheader()  # Write header row
	writer.writerows(rows)  # Write data rows
print(f"CSV write time: {time() - word_start} seconds")
print(f"Total runtime: {time() - start_time} seconds")