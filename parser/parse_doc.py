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
import csv, os, sys, re, json
import urllib.request
from collections import defaultdict

OUTPUT_DIR_PFX = "../corpus/"
TOKENS_DIR = "tokens"
HTML_DIR = "texts"
SECTIONS_FILE = "sections.json" # Name of file containing sections of document (in document root dir)

def parse_doc(input_text: str, output_path: str):
    '''
    Docstring for parse_doc
    
    :param input_text: Full text of document to parse
    :type input_text: str
    :param output_path: path of .csv file for writing output
    :type output_path: str
    '''
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
    updated_rows = get_line_annotations(input_text, rows, output_path)
    column_headers = column_headers + ["book_num", "chapter_num", "line_num", "doc_token_index"]
    assert 'book_num' in updated_rows[0]

    # Write output
    with open(output_path, "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=column_headers)
        writer.writeheader()  # Write header row
        writer.writerows(updated_rows)  # Write data rows
    print(f"CSV write time: {time() - word_start} seconds")
    print(f"Total runtime: {time() - start_time} seconds")

    # Return row data
    return updated_rows

def get_line_annotations(annotated_text: str, parsed_text: list, output_path: str) -> list:
    '''
	Append book, chapter, & line number data to CLTK parse output
	
	:param annotated_text: Original Tess text file with line annotations
	:type annotated_text: str
	:param parsed_text: CLTK output dictionary
	:type parsed_text: list
    :param output_path: Name of output file (to be passed to HTML parser)
    :type output_path: str
	:return: CLTK dictionary appended with columns for book, chapter, & line number for each token
	:rtype: list
	'''
    lines = annotated_text.splitlines()
    
    # Index of token for iterating through CLTK tokens (also used for recording index of token within document)
    cltk_idx = 0  

    # List for storing data to be passed to HTML parser
    html_lines = []
    
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
        line_tokens = []
        while len(line_clean) > 0:
            token = parsed_text[cltk_idx]
            token_str = unicodedata.normalize("NFC", token["string"])
            if not line_clean.startswith(token_str):
                raise ValueError(f"Word did not match CLTK token.\nToken: '{token['string']}' ({token['string'].encode('utf-8').hex()})\nline (remaining): '{line_clean}'\n({line_clean.encode('utf-8').hex()}\nline (complete): '{line}'")
            token["book_num"] = bk_num
            token["chapter_num"] = ch_num if ch_num is not None else "\\N"
            token["line_num"] = ln_num
            token["doc_token_index"] = cltk_idx

            # Append token string to tokens list (for HTML)
            if str(token['pos']) != 'punctuation':
                line_tokens.append({ 'token':token_str, 'value':cltk_idx })
            else: 
                line_tokens.append({ 'token':token_str, 'value':None })

            # Update indices, consume text from line_clean
            cltk_idx += 1
            line_clean = line_clean[len(token["string"]):]

            # Consume extraneous characters; append to null token for HTML
            null_token = ''
            while (True):
                if line_clean.startswith((' ',  '“', '”')):
                    null_token += line_clean[0]
                    line_clean = line_clean[1:]
                elif line_clean.startswith('que') and not parsed_text[cltk_idx]['string'].startswith('que'):
                    # Handle -que enclitic - sometimes not parsed by CLTK?
                    null_token += 'que'
                    line_clean = line_clean[len('que'):]
                else: 
                    break
            if null_token != '':
                line_tokens.append({ 'token':null_token, 'value':None })
        html_lines.append({
            'tokens': line_tokens,
            'book': bk_num,
            'chapter': ch_num,
            'line': ln_num
        })
    
    html_path = os.path.dirname(output_path).replace(f'/{TOKENS_DIR}/', f'/{HTML_DIR}/', 1)
    process_doc(html_lines, html_path)
    return parsed_text

def process_doc(input_data: list, parent_dir: str):
    '''
    Document processor to generate JSON of token data to be passed to for frontend, linked to parsed tokens
    
    :param input_data: list of text line dictionaries (from get_line_annotations)
    :type input_text: str
    :param html_path: Name of output file
    :type html_path: str
    '''
    # Convert token dicts to JSON
    def nested_dict():
        '''
        Custom nested dict class
        (allow deep assignment without initializing parents first)

        Solution generated via Google AI, 
        derived from https://stackoverflow.com/questions/22455384/assign-nested-keys-and-values-in-dictionaries
        '''
        return defaultdict(nested_dict)
    
    output_json = nested_dict()
    # Set JSON schema
    has_book = False
    has_chapter = False
    if input_data[0]['book'] != "\\N":
        has_book = True
    if input_data[0]['chapter'] != "\\N":
        has_chapter = True
        assert has_book
    assert input_data[0]['line'] != "\\N"
    for line in input_data:
        bk_num = line['book']
        ch_num = line['chapter']
        ln_num = line['line']
        if has_chapter:
            assert bk_num != "\\N" and ch_num != "\\N" and ln_num != "\\N"
            output_json[bk_num][ch_num][ln_num] = []
            for token in line['tokens']: 
                output_json[bk_num][ch_num][ln_num].append(token)
        elif has_book:
            assert bk_num != "\\N" and ln_num != "\\N"
            output_json[bk_num][ln_num] = []
            for token in line['tokens']: 
                output_json[bk_num][ln_num].append(token)
        else:
            assert ln_num != "\\N"
            output_json[ln_num] = []
            for token in line['tokens']: 
                output_json[ln_num].append(token)

    # Write output to files
    section_names = []
    if has_book:
        # If book data, divide files
        for book, token_dict in output_json.items():
            # Generate output file
            if has_chapter:
                # If first two levels of token_dict are not token level (i.e. token_dict has chapter values),
                # Create individual files per chapter
                book_chapters = []
                for chapter, line_dict in token_dict.items(): 
                    output_dir = os.path.join(parent_dir, book)
                    section_name = f'{book}-{chapter}'
                    book_chapters.append(section_name)
                    output_file = os.path.join(output_dir, f'{section_name}.json')
                    os.makedirs(output_dir, exist_ok=True)
                    with open(output_file, 'w') as f: 
                        json.dump(line_dict, f)
                section_names.append({
                    'book': book,
                    'chapters': book_chapters
                })
            else: 
                # Create files by book
                output_dir = parent_dir
                section_names.append({
                    'book': book,
                    'chapters': None
                })
                output_file = os.path.join(output_dir, f'{book}.json')
                os.makedirs(output_dir, exist_ok=True)
                with open(output_file, 'w') as f: 
                    json.dump(token_dict, f)
    else: 
        # No book numbers
        output_dir = parent_dir
        section_names.append({
            'book': None,
            'chapters': None
        })
        output_file = os.path.join(output_dir, 'tokens.json')
        os.makedirs(output_dir, exist_ok=True)
        with open(output_file, 'w') as f: 
            json.dump(output_json, f)
    
    # Update section names file
    sections_path = os.path.join(parent_dir, SECTIONS_FILE)
    if os.path.exists(sections_path):
        try:
            with open(sections_path, 'r') as rf:
                try:
                    existing_sections = json.load(rf)
                except (json.JSONDecodeError, ValueError):
                    existing_sections = []
        except FileNotFoundError:
            existing_sections = []
        if isinstance(existing_sections, list):
            section_names = existing_sections + section_names
    with open(sections_path, 'w') as f:
        json.dump(section_names, f)


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
    output_dir = os.path.join(OUTPUT_DIR_PFX, TOKENS_DIR, author, work)
    html_dir = os.path.join(OUTPUT_DIR_PFX, HTML_DIR, author, work)
    output_file = os.path.join(output_dir, filename.rstrip(".tess") + ".csv")
    # Create output dir if not exists
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(html_dir, exist_ok=True)

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
    print("Output path:", output_file + ".csv")
    print("Approximate token count:", len(full_text.split()))
    print()
    parse_doc(full_text, output_file)