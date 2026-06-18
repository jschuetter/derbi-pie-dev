'''
xmlreader.py

Python script to read dictionary XML file for 
Monier-Williams Sanskrit-English dictionary
'''

import csv, re, os
import mysql.connector
from lxml import etree
from time import time

from lexdata import *

# XSLT_DOC = "./monier-williams-template.xslt"
SQL_NULL = "\\N"

def get_entries(filename): 
    '''
    Return a dict of entries from the provided
    XML file
    '''
    parser = etree.XMLParser(load_dtd=True, no_network=False)
    tree = etree.parse(filename, parser=parser)
    root = tree.getroot()  # <mw> entry
    
    # Zoega dictionary XML does not include the following fields: 
    # page_num, orthography, components, stem, etymology

    # Lang code, editor, updated date fields will be filled in when
    # importing to MySQL

    dict_entries = []
    # xslt_tree = etree.parse(XSLT_DOC)
    # xslt = etree.XSLT(xslt_tree)

    # Maintain lists of (lemma_id, lemma) pairs that
    # were found, not found or multiples found in MySQL
    # Will be exported to JSON format when execution finishes
    matched_lemmas = []  # dict format: {lemma_id, lemma, entry, orig_lemma, orig_entry}
    unmatched_lemmas =  []  # dict format: {lemma_id, lemma, entry} (new ID generated)
    multiple_match_lemmas = []  # dict format: {lemma_id, lemma, entry, matches (list of entries in same format)}


    # Init. MySQL connection
    conn = mysql.connector.connect(
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASS'),
        host=os.getenv('MYSQL_HOST'),
        database=os.getenv('MYSQL_DB')
        )
    db = conn.cursor()

    # Sequential idx counter for unmatched entries - prepended with "*" in dict
    unknown_lemma_idx = 1
    unknown_sense_idx = 1

    # Next available indices in MySQL
    db.execute((
        "SELECT MAX(lemma_id) FROM lex_master "
        "WHERE lang = 'Skt.';"
    ))
    next_lemma_idx = db.fetchone()[0] + 1
    db.execute((
        "SELECT MAX(sense_id) FROM lex_senses "
        "WHERE lang = 'Skt.';"
    ))
    next_sense_idx = db.fetchone()[0] + 1
    print("Next available indices:", next_lemma_idx, "(lemmas),", next_sense_idx, "(senses)")

    prev_entry = None
    prev_main_entry = None
    
    # Parse XML line-by-line
    # Cases: 
    #   1. Create new headword entry
    #       - If subordinate: link to headword entry
    #   2. Create new sense entry
    #   3. Append to previous entry

    for entry in root: 
        new_entry = {
            "lemma_id": f"*{unknown_lemma_idx}",
            "lemma": "",
            "lemma_normalized": "",
            "lemma_translit": "",
            "sense_num": "",
            "page_num": "",
            "type": "",
            "orthography": "",
            "ipa": "",
            "pos": "",
            "gender": "",
            "stem": "",
            "etymology": "",
            "etymology_resolved": "",
            "entry": "",
            "entry_str": "",
            "components": "",
            "gloss": "",
            "entry_type": "",
            "related": "",
            # Senses only
            "sense_id": "",
            "h_num": "",
            "parent_h_num": "",
        }

        # Entry has 1 of 13 root tags; will determine course of action
        # Case 1: new headword (<H1>)
        # Create new headword
        if entry.tag == "H1":
            senses_count = 0
            new_entry.update({
                "type": "main",
            })
        # Case 2: subordinate headword (<H2>, <H3>, <H4>)
        # Create new headword, link to primary entry
        elif re.match(r'H[2-4]', entry.tag):
            senses_count = 0
            if prev_main_entry is None: 
                raise ValueError(f"Prev. entry is None.\nLine: {etree.tostring(entry, encoding="Unicode")}")
            new_entry.update({
                "type": "main",
                "related": prev_main_entry["lemma_id"],
            })
        # Case 3: sub-sense of previous entry (<H1A>, <H2A>, <H2B>, etc.)
        # Create new sub-sense
        elif re.match(r'H[1-4][A-B]', entry.tag):
            new_entry.update({
                "type": "sense",
                "lemma_id": prev_entry["lemma_id"],
                "sense_id": f"*{unknown_sense_idx}",
                "h_num": f"n{prev_entry["lemma_id"]}.{senses_count}",
            })
        else: 
            raise ValueError(f"Unexpected entry root tag: {entry.tag}")

        # TODO: fill in other entry info HERE (before indexing)
        # Parse header: lemma & orthography
        hdr_tag = entry[0]
        assert hdr_tag.tag == "h"
        assert hdr_tag[0].tag == "key1"
        lemma_normalized_slp1 = hdr_tag[0].text
        lemma_normalized_deva = slp1_to_deva(lemma_normalized_slp1)
        lemma_normalized_iast = slp1_to_iast(lemma_normalized_slp1)
        assert hdr_tag[1].tag == "key2"
        lemma_slp1 = hdr_tag[1].text
        lemma_deva = slp1_to_deva(lemma_slp1.replace("-", ""))
        orth_iast = slp1_to_iast(lemma_slp1)
        orth_deva = slp1_to_deva(lemma_slp1)
        # Update entry
        new_entry.update({
            "lemma": lemma_deva,
            "lemma_normalized": lemma_normalized_deva,
            "lemma_translit": lemma_normalized_iast,
            "orthography": f"{orth_iast} ({orth_deva})",
        })

        # Process entry body
        body_tag = entry[1]
        assert body_tag.tag == "body"
        # Look for lexical information (info tag at end of <body>)
        for idx in range(len(body_tag)-1, -1, -1): 
            child = body_tag[idx]
            if child.tag == "info": 
                if child.get("lex") is not None:
                    if child.get("lex") == "inh":
                        new_entry["gender"] = prev_entry["gender"]
                    else: 
                        new_entry["gender"] = child.get("lex").replace(":", "") + "."

        # TODO: build XSLT template for converting body tags?
        # e.g. <s>, <lex>, <ls>, <info>
        new_entry["entry"] = f'<div class="sanskrit bodytext">{body_tag.__str__()}</div>'
        new_entry["entry_str"] = "".join(body_tag.itertext())
        
        # TODO: check for sub-senses contained within entry body
        # (e.g. '; <div n="to" />' )

        # Process tail tag
        tail_tag = entry[2]
        assert tail_tag.tag == "tail"
        assert tail_tag[1].tag == "pc"
        new_entry["page_num"] = tail_tag[1].text.split(",")[0]

        # Try to retrieve lemma_id from MySQL
        print("Lemma/pg:", new_entry["lemma_translit"], "/", new_entry["page_num"])
        if new_entry["type"] != "sense":
            lemma_query = (
                "SELECT lemma_id, lemma, entry_str FROM lex_master "
                "WHERE lemma LIKE %s "
                "AND page_num = %s"
            )
            db.execute(lemma_query, (f"{new_entry["lemma_translit"]} (%)", new_entry["page_num"]))
            lemma_matches = db.fetchall()
            print("Matches:", *lemma_matches)
            if len(lemma_matches) > 1: 
                # Many matches; need to remediate manually
                multiple_match_lemmas.append({
                    "lemma_id": new_entry["lemma_id"],
                    "lemma": new_entry["lemma_translit"],
                    "entry_str": new_entry["entry_str"],
                    "matches": [
                        {
                            "lemma_id": row[0],
                            "lemma": row[1],
                            "entry_str": row[2]
                        } for row in lemma_matches
                    ]
                })
            elif len(lemma_matches) < 1: 
                # No match found
                new_entry["lemma_id"] = next_lemma_idx
                unmatched_lemmas.append({
                    "lemma_id": next_lemma_idx,
                    "lemma": new_entry["lemma_translit"],
                    "entry_str": new_entry["entry_str"]
                })
                next_lemma_idx += 1
            else: 
                # Exactly one match found
                assert len(lemma_matches) == 1

                # TODO: add assertion to check that lemma does actually match

                new_entry["lemma_id"] = lemma_matches[0][0]
                matched_lemmas.append({
                    "lemma_id": new_entry["lemma_id"],
                    "lemma": new_entry["lemma_translit"],
                    "entry_str": new_entry["entry_str"],
                    "orig_lemma": lemma_matches[0][1],
                    "orig_entry_str": lemma_matches[0][2],
                })

        # Final processing
        if entry.tag == "H1": 
            prev_main_entry = entry
        if new_entry["type"] != "sense": 
            prev_entry = entry
            
        new_entries = [new_entry] # + new_subentries
        for ne in new_entries: 
            for k,v in ne.items():
                # Convert empty fields to SQL_NULL
                if v == "":
                    ne[k] = SQL_NULL
            dict_entries.append(ne)

        # Increment lemma_idx for each definition
        unknown_lemma_idx += 1
        unknown_sense_idx += 1

        # TODO DEV: RETURN EARLY
        print(dict_entries)
        return

    # TODO: write entry matching lists to JSON files for review/remediation
        
    return dict_entries

def save_csv(data, filename):
    fieldnames = ["lemma_id", "lemma", "sense_num", "type", "ipa", "pos", "gender", "entry", "entry_str", "gloss", "sense_id", "h_num", "parent_h_num"]
    rows = [{
        "lemma_id": ent["lemma_id"],
        "lemma": ent["lemma"], 
        "sense_num": ent["sense_num"],
        "type": ent["type"],
        "ipa": ent["ipa"], 
        "pos": ent["pos"],
        "gender": ent["gender"],
        "entry": ent["entry"],
        "entry_str": ent["entry_str"],
        "gloss": ent["gloss"],
        "sense_id": ent["sense_id"],
        "h_num": ent["h_num"],
        "parent_h_num": ent["parent_h_num"]
        } for ent in data]
    with open(filename, "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()  # Write header row
        writer.writerows(rows)  # Write data rows

if __name__ == "__main__":
    startTime = time()
    entries = get_entries("monier-williams.xml")
    if entries is not None: 
        save_csv(entries, "monier-williams.csv")
    print("Parsing completed.")
    print("Runtime:", time() - startTime, "s")
