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

import unicodedata

from time import time
import csv, os, sys, re
import urllib.request

OUTPUT_DIR_PFX = "../corpus/parsed/"

def parse_doc(input_text: str, output_path: str):
    # Clean line annotations from text for CLTK parsing
    clean_text = re.sub(r'^\<[ a-zA-Z0-9.\-]*\>\s', '', input_text, flags=re.MULTILINE)
    
    # Load pipeline for Latin
    cltk_nlp = NLP(language="lat", suppress_banner=True)
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
    cltk_doc = cltk_nlp.analyze(text=clean_text)
    print(f"Parsing time: {time() - start_time} seconds")
    print("Tokens parsed:", len(cltk_doc.words))
    print("Sentences parsed:", len(cltk_doc.sentences_tokens))

    # Write Word data to CSV
    word_start = time()
    column_headers = [
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
        for key in column_headers:
            val = getattr(w, key)
            if (
                isinstance(val, cltk.morphology.morphosyntax.MorphosyntacticFeatureBundle) and len(val) == 0 or 
                val in ["{}", "[]", ""]
            ):
                row[key] = sqlNull
            else: 
                row[key] = val
        rows.append(row)

	# Retrieve line data & append to rows
    updated_rows = get_line_annotations(input_text, rows)
    column_headers = column_headers + ["book_num", "chapter_num", "line_num"]
    assert 'book_num' in updated_rows[0]

    # Write output
    with open(output_path, "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=column_headers)
        writer.writeheader()  # Write header row
        writer.writerows(updated_rows)  # Write data rows
    print(f"CSV write time: {time() - word_start} seconds")
    print(f"Total runtime: {time() - start_time} seconds")

def get_line_annotations(annotated_text: str, parsed_text: list) -> list:
    '''
	Append book, chapter, & line number data to CLTK parse output
	
	:param annotated_text: Original Tess text file with line annotations
	:type annotated_text: str
	:param parsed_text: CLTK output dictionary
	:type parsed_text: list
	:return: CLTK dictionary appended with columns for book, chapter, & line number for each token
	:rtype: list
	'''
    lines = annotated_text.splitlines()
    
    line_idx = 0
    cltk_idx = 0  # Index of token for iterating through CLTK tokens
    for line_idx in range(len(lines)): 
        # Normalize under Unicode NFC convention to handle precomposed characters
        line = unicodedata.normalize("NFC", lines[line_idx])
        # Skip empty lines (e.g. at end)
        if not len(line) or line.isspace():
            continue
        # next_line = lines[line_idx+1] if line_idx < len(lines) - 1 else None
        # Extract book, chapter, line numbers from line annotation
        m = re.search(r'<[^>]*?(\d+(?:\-\d+)?)(?:\.([a-zA-Z0-9]+))?(?:\.(\d+))?>', line)
        if m:
            # If 3 digits
            if m.group(3) is not None:
                bk_num, ch_num, ln_num = m.group(1,2,3)
            # If 2 digits
            elif m.group(2) is not None: 
                bk_num, ln_num = m.group(1,2)
                ch_num = "\\N"
            # If 1 digit
            else:
                ln_num = m.group(1)
                bk_num = ch_num = "\\N"
        else:
            bk_num = ch_num = ln_num = None
            raise ValueError("Unable to find annotations for line " + line)
        
        # Strip annotations from line
        line_clean = re.sub(r'^\<[ a-zA-Z0-9.\-]*\>\s', '', line, flags=re.MULTILINE)
        line_clean = line_clean.lstrip(' “”')
        while len(line_clean) > 0:
            token = parsed_text[cltk_idx]
            token_str = unicodedata.normalize("NFC", token["string"])
            if not line_clean.startswith(token_str):
                raise ValueError(f"Word did not match CLTK token.\nToken: '{token['string']}' ({token['string'].encode('utf-8').hex()})\nline (remaining): '{line_clean}'\n({line_clean.encode('utf-8').hex()}\nline (complete): '{line}'")
            token["book_num"] = bk_num
            token["chapter_num"] = ch_num if ch_num is not None else "\\N"
            token["line_num"] = ln_num

            # Update indices, consume text from line_clean
            cltk_idx += 1
            line_clean = line_clean[len(token["string"]):]
            line_clean = line_clean.lstrip(' “”')
            # Handle -que enclitic - sometimes not parsed by CLTK?
            if line_clean.startswith('que') and not parsed_text[cltk_idx]['string'].startswith('que'): 
                line_clean = line_clean[len('que'):]
                line_clean = line_clean.lstrip(' “”')


    return parsed_text


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

    print("Loaded file", filename)
    print("Output path:", outputFile)
    print("Approximate token count:", len(full_text.split()))
    print()
    parse_doc(full_text, outputFile)