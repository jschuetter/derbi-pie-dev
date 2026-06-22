'''
xmlreader.py

Python script to read dictionary XML file for 
Monier-Williams Sanskrit-English dictionary
'''

import csv, re, os
from lxml import etree
from copy import deepcopy
from time import time

from lexdata import *

XSLT_DOC = "./monier-williams-template.xslt"
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
    # Init. XSLT template, method namespace
    xslt_tree = etree.parse(XSLT_DOC)
    xslt = etree.XSLT(xslt_tree)

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
        lemma_deva = slp1_to_deva(lemma_slp1.replace("-", "").replace("—", ""))
        orth_iast = slp1_to_iast(lemma_slp1)
        orth_deva = slp1_to_deva(lemma_slp1)

        # Parse out components, if present
        components = ""
        if "-" in orth_iast or "—" in orth_iast: 
            components = f"{orth_iast.replace("-", "|").replace("—", "|")} ({orth_deva.replace("-", "|").replace("—", "|")})"

        if len(hdr_tag) > 2:
            assert hdr_tag[2].tag == "hom"
            new_entry["sense_num"] = hdr_tag[2].text
        # Update entry
        new_entry.update({
            "lemma": lemma_deva,
            "lemma_normalized": lemma_normalized_deva,
            "lemma_translit": lemma_normalized_iast,
            "orthography": f"{orth_iast} ({orth_deva})",
            "components": components,
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
                        lex_info = child.get("lex")
                        # Replace parentheses & transcribe, if necessary
                        lex_info = re.sub(r'#(.*?):', lambda m : f"({slp1_to_iast(m.group(1))})", lex_info)
                        new_entry["gender"] = lex_info.replace(":", "") + "."
        
        # Check for sub-senses contained within entry body
        body_tag, new_subentries = parse_senses(new_entry, body_tag, xslt=xslt)

        entry_inner = xslt(body_tag).__str__().replace(">\n", ">")
        # Strip initial homonym number
        entry_inner = re.sub(r'^\s?<span class="hom">[0-9]+\.</span>\s?', '', entry_inner)
        new_entry["entry"] = f'<div class="sanskrit bodytext">{entry_inner.strip()}</div>'
        # Handle transliteration in <s> tags
        if "<s>" in new_entry["entry"]:
            new_entry["entry"] = re.sub(r'<s>(.*?)</s>', lambda m : f'<span class="s">{slp1_to_iast(m.group(1))}</span>', new_entry["entry"])

            # Parse entry string from entry field to preserve transliteration
            new_entry["entry_str"] = re.sub(r'<.*?>', '', new_entry["entry"])
        else: 
            new_entry["entry_str"] = "".join(body_tag.itertext()).strip()

        # Process tail tag
        tail_tag = entry[2]
        assert tail_tag.tag == "tail"
        assert tail_tag[1].tag == "pc"
        new_entry["page_num"] = tail_tag[1].text.split(",")[0]

        # Copy page num to subentries & add indices
        if new_subentries: 
            for se in new_subentries: 
                se.update({
                    "page_num": new_entry["page_num"],
                    "lemma_id": prev_entry["lemma_id"],
                    "sense_id": f"*{unknown_sense_idx}",
                    "h_num": f"n{prev_entry["lemma_id"]}.{senses_count}",
                })
                unknown_sense_idx += 1
                senses_count += 1

        # TODO: fill in gloss field??

        # Final processing
        # Set previous entry of appropriate level, unset lower levels
        if re.fullmatch(r'H[1-4]', entry.tag):
            entry_lvl = int(entry.tag[-1])
            prev_entry_lvl[entry_lvl] = new_entry
            
            for lvl in range(entry_lvl+1, 5):
                prev_entry_lvl[lvl] = None
                
        if new_entry["type"] != "sense": 
            prev_entry = new_entry
            
        new_entries = [new_entry] + new_subentries
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

def parse_senses(parent_entry, body_tag, *, xslt): 
    '''
    Helper method to parse senses out from within single entry line
    
    :param dict parent_entry: parent new_entry dict (for copying to subentries)
    :param etree.Element body_tag: entry body as etree.Element
    :param etree.XSLT xslt: XSLT parser instance from parent scope

    :return tuple: 
    (new_body, new_subentries)
    - new_body: body tag with subentries removed
    - new_subentries: new sense entries, to be added to output 
    
    *(N.B. page_num & indexing fields handled in parent scope!)*
    '''

    '''
    Delimiters: 
    - ' <div n="to"/>'
    - ' <div n="P"/>'
    - ' <div n="P"/>'
    - ' <div n="p"/>'
    - ' <div n="1"/>'
    - ' : <div n="vp"/><ab>'
    - '; <div n="vp"/>'
    '''

    # Check for delimiters
    senses_list = re.split(r'<div n=".*?"/>', etree.tostring(body_tag, encoding="Unicode"))
    if len(senses_list) == 1: 
        return (body_tag, [])

    # Handle <body> tag matching
    new_body = etree.XML(senses_list[0] + "</body>")
    senses_list[-1] = senses_list[-1].replace("</body>", "")

    # Process sensess separately
    new_subentries = []
    for sense_idx in range(1, len(senses_list)):
        new_sense = deepcopy(parent_entry)
        new_sense["type"] = "sense"
        sense_str = f"<body>{senses_list[sense_idx].strip()}</body>"
        sense_elem = etree.XML(sense_str)
        entry_inner = xslt(sense_elem).__str__().replace(">\n", ">")
        new_sense["entry"] = f'<div class="sanskrit bodytext">{entry_inner.strip()}</div>'
        # Handle transliteration in <s> tags
        if "<s>" in new_sense["entry"]:
            new_sense["entry"] = re.sub(r'<s>(.*?)</s>', lambda m : f'<span class="s">{slp1_to_iast(m.group(1))}</span>', new_sense["entry"])

            # Parse entry string from entry field to preserve transliteration
            new_sense["entry_str"] = re.sub(r'<.*?>', '', new_sense["entry"])
        else: 
            new_sense["entry_str"] = "".join(sense_elem.itertext()).strip()

        new_subentries.append(new_sense)

    return (new_body, new_subentries)


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
