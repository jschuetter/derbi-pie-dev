'''
xmlreader.py

Python script to read dictionary XML file for 
Monier-Williams Sanskrit-English dictionary
'''

import csv, re, os
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

    # Sequential idx counter for unmatched entries - prepended with "*" in dict
    # N.B. must re-index all after parsing XML to match existing indices in MySQL
    unknown_lemma_idx = 1
    unknown_sense_idx = 1

    prev_entry = None
    # Previous entry at each <H?> level
    # N.B. index 0 will always be None, by convention
    prev_entry_lvl = [None, None, None, None, None]
    
    # Parse XML line-by-line
    # Cases: 
    #   1. Create new headword entry
    #   2. Create new subordinate form entry, link to parent
    #   3. Create new sense entry

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
        # Case 2: subordinate headword 
        # (<H2>, <H3>, <H4> ~or~ <H?B>, <H?C>)
        # Create new headword, link to primary entry
        elif re.fullmatch(r'H[2-4][B-C]?|H1[B-C]', entry.tag):
            senses_count = 0
            entry_lvl = int(re.match(r'H([1-4])', entry.tag).group(1))
            if re.fullmatch(r'H[1-4][B-C]', entry.tag):
                # If entry tag ends in B or C, parent entry is 
                # at "same" lvl (e.g. <H2> parent <H2B>)
                parent_lvl = entry_lvl
            else: 
                # Else, parent level is one above
                # (e.g. <H1> parents <H2>)
                parent_lvl = entry_lvl - 1
            # Find level of nearest nonnull parent entry
            while prev_entry_lvl[parent_lvl] is None: 
                parent_lvl -= 1
            new_entry.update({
                "type": "main",
                "related": prev_entry_lvl[parent_lvl]["lemma_id"],
            })
        # Case 3: sub-sense of previous entry (<H1A>, <H2A>, <H1E>, etc.)
        # Create new sub-sense
        # Note: <H?E> lines are etymology data only -- parsing as sub-sense for now.
        elif re.fullmatch(r'H[1-4][AE]', entry.tag):
            new_entry.update({
                "type": "sense",
                "lemma_id": prev_entry["lemma_id"],
                "sense_id": f"*{unknown_sense_idx}",
                "h_num": f"n{prev_entry["lemma_id"]}.{senses_count}",
            })
            unknown_sense_idx += 1
            senses_count += 1
        else: 
            raise ValueError(f"Unexpected entry root tag: {entry.tag}")

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
        # TODO: default transcriber DOES NOT transcribe '/' as udatta and "'" as avagraha
        orth_iast = slp1_to_iast(lemma_slp1)
        orth_deva = slp1_to_deva(lemma_slp1)
        if len(hdr_tag) > 2:
            assert hdr_tag[2].tag == "hom"
            new_entry["sense_num"] = hdr_tag[2].text
        # Update entry
        # TODO: parse out components
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
                    new_entry["pos"] = "n."
                    if child.get("lex") == "inh":
                        new_entry["gender"] = prev_entry["gender"]
                    else: 
                        new_entry["gender"] = child.get("lex").replace(":", "") + "."

        # TODO: build XSLT template for converting body tags?
        # e.g. <s>, <lex>, <ls>, <info>
        # TODO: N.B. want to do transliteration on text inside <s> tags
        new_entry["entry"] = f'<div class="sanskrit bodytext">{((body_tag.text or "") + "".join([(child.text or "") for child in body_tag])).strip()}</div>'
        new_entry["entry_str"] = "".join(body_tag.itertext()).strip()
        
        # TODO: check for sub-senses contained within entry body
        # (e.g. '; <div n="to" />' )

        # Process tail tag
        tail_tag = entry[2]
        assert tail_tag.tag == "tail"
        assert tail_tag[1].tag == "pc"
        new_entry["page_num"] = tail_tag[1].text.split(",")[0]

        # Final processing
        # Set previous entry of appropriate level, unset lower levels
        if re.fullmatch(r'H[1-4]', entry.tag):
            entry_lvl = int(entry.tag[-1])
            prev_entry_lvl[entry_lvl] = new_entry
            
            for lvl in range(entry_lvl+1, 5):
                prev_entry_lvl[lvl] = None
                
        if new_entry["type"] != "sense": 
            prev_entry = new_entry
            
        new_entries = [new_entry] # + new_subentries
        for ne in new_entries: 
            for k,v in ne.items():
                # Convert empty fields to SQL_NULL
                if v == "":
                    ne[k] = SQL_NULL
            dict_entries.append(ne)

        # Increment lemma_idx for each definition
        if new_entry["type"] != "sense":
            unknown_lemma_idx += 1

    return dict_entries

def save_csv(data, filename):
    fieldnames = ["lemma_id", "lemma", "lemma_normalized", "lemma_translit", "sense_num", "page_num", "type", "orthography", "pos", "gender", "entry", "entry_str", "components", "gloss", "related", "sense_id", "h_num", "parent_h_num"]
    rows = [{
        "lemma_id": ent["lemma_id"],
        "lemma": ent["lemma"], 
        "lemma_normalized": ent["lemma_normalized"], 
        "lemma_translit": ent["lemma_translit"], 
        "sense_num": ent["sense_num"],
        "page_num": ent["page_num"],
        "type": ent["type"],
        "orthography": ent["orthography"], 
        "pos": ent["pos"],
        "gender": ent["gender"],
        "entry": ent["entry"],
        "entry_str": ent["entry_str"],
        "components": ent["components"],
        "gloss": ent["gloss"],
        "related": ent["related"],
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
    save_csv(entries, "monier-williams.csv")
    print("Parsing completed.")
    print("Runtime:", time() - startTime, "s")
