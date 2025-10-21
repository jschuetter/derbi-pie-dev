'''
parse-doc.py
03 October 2025

Document parsing script - version 2

21 Oct 2025 - add parsing from URL, create method for bulk parsing
'''

import cltk
from cltk import NLP
from cltk.phonology import syllabifier_processes, transcription_processes
from cltk.dependency.tree import DependencyTree

from time import time
import csv, os, sys, re
import urllib.request

OUTPUT_DIR_PFX = "corpus/parsed/"

def parse_doc(input_text: str, output_path: str):
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
	# Add other processes
	# cltk_nlp.pipeline.processes.append(cltk.ner.processes.LatinNERProcess)  # NER unavailable for Latin?
	cltk_nlp.pipeline.processes.append(syllabifier_processes.LatinSyllabificationProcess)
	cltk_nlp.pipeline.processes.append(transcription_processes.LatinPhonologicalTranscriberProcess)
	cltk_nlp.pipeline.processes.append(cltk.stem.processes.LatinStemmingProcess)
	print("Final pipeline:", cltk_nlp.pipeline.processes)

	# Analyze text
	start_time = time()
	print("Parsing...")
	cltk_doc = cltk_nlp.analyze(text=input_text)
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

	# Write output
	with open(output_path, "w", newline='') as f:
		writer = csv.DictWriter(f, fieldnames=COLUMN_HEADERS)
		writer.writeheader()  # Write header row
		writer.writerows(rows)  # Write data rows
	print(f"CSV write time: {time() - word_start} seconds")
	print(f"Total runtime: {time() - start_time} seconds")


if __name__ == "__main__":
	# Get input file from CLI arg
	if len(sys.argv) < 2: 
		raise ValueError("Provide an input file as a filepath or URL as the first command-line argument.")
	inputFile = sys.argv[1]
	isUrl = False
	if inputFile.startswith("https://"):
		isUrl = True

	if not inputFile.endswith(".tess"):
		raise ValueError("This script is designed to work with Tesserae project files. Please provide a compatible file.")

	# Parse output file from filename
	filename = inputFile.split("/")[-1]
	author, work, *_ = filename.split(".")
	outputDir = os.path.join(OUTPUT_DIR_PFX, author, work)
	outputFile = os.path.join(outputDir, filename.rstrip(".tess") + ".csv")
	# Create output dir if not exists
	os.makedirs(outputDir, exist_ok=True)

	# Read document
	full_text = None
	if isUrl:
		with urllib.request.urlopen(inputFile) as res:
			full_text = res.read().decode('utf-8')
	else:
		with open(inputFile) as text:
			full_text = text.read()
	# Test response
	# print(full_text[:500])

	# Clean document
	# Remove the section in angle brackets at the beginning of each line
	clean_text = re.sub(r'^\<[ a-zA-Z0-9.]*\>\s', '', full_text, flags=re.MULTILINE)
	# Test text
	# print(clean_text[:500])
	print("Loaded file", filename)
	print("Output path:", outputFile)
	print("Approximate token count:", len(clean_text.split()))
	print()
	parse_doc(clean_text, outputFile)