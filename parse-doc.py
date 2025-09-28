'''
parse-doc.py
27 September 2025

Document parsing script - version 1.
'''

import cltk
from cltk import NLP
from cltk.phonology import syllabifier_processes, transcription_processes
from cltk.dependency.tree import DependencyTree

from time import time
import csv, os

INPUT_FILE = "corpus/latin/livy.ab_urbe_condita.book_1.sty"
OUTPUT_FILE = "corpus/parsed/livy/ab_urbe_condita/1.csv"

# Read document
with open(INPUT_FILE) as text:
	full_text = text.read()
	# Cut down document length for demo
	print("Approximate token count:", len(full_text.split()))

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
# Remove lexicon process for time's sake
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
cltk_doc = cltk_nlp.analyze(text=full_text)
end_time = time()
print(f"Execution time: {end_time - start_time} seconds")
print("Tokens parsed:", len(cltk_doc.words))
print("Sentences parsed:", len(cltk_doc.sentences_tokens))

# Print analysis results
print(type(cltk_doc))
print([x for x in dir(cltk_doc) if not x.startswith("__")])  #Print all accessors
# Print a few useful accessors
print(cltk_doc.tokens[:20])
print(cltk_doc.lemmata[:20])
print(cltk_doc.pos[:20])   #parts-of-speech
print(cltk_doc.sentences_tokens[:2])  #First two sentences

# Examine sentence & single word using Doc.words accessor
sentence = cltk_doc.sentences[6]  # type: List[Word]
sentence_str = cltk_doc.sentences_strings[6]  # type: str
print("Original sentence:", sentence_str)
print()
word_str = "concurrunt"
word = [w for w in cltk_doc.words if w.string == word_str][0]
print(f"Properties of Word '{word_str}'")
print(word)

# Analyze second word
word_str = "nomen"
word = [w for w in cltk_doc.words if w.string == word_str][0]
print(f"Properties of Word '{word_str}'")
print(word)

# Syntax modeling
print("Sentence (same as above):", sentence_str)
syntax_tree = DependencyTree.to_tree(sentence)
syntax_tree.print_tree()

# Write to CSV
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
# rows = [{
# 	"index_char_start": w["index_char_start"],
# 	"index_char_stop": w["index_char_stop"],
# 	"index_token": w["index_token"],
# 	"index_sentence",
# 	"string",
# 	"pos",
# 	"lemma",
# 	"stem",
# 	"dependency_relation",
# 	"governor_index",
# 	"features",
# 	"category",
# 	"syllables",
# 	"phonetic_transcription"
#         } for w in cltk_doc.words.items()]

# Create files if not existent
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
with open(OUTPUT_FILE, "w", newline='') as f:
	writer = csv.DictWriter(f, fieldnames=COLUMN_HEADERS)
	writer.writeheader()  # Write header row
	writer.writerows(rows)  # Write data rows