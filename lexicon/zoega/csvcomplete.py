'''
csvcomplete.py
A web scraping script to fill in gaps in the Zoega XML
(i.e. missing entries)
'''

import csv, requests, re
from lxml import html
from lxml.etree import strip_tags
from time import time

def scrape_entry(data):
    '''
    Attempt to scrape the Zoega definition for the given data row
    from https://old-icelandic.vercel.app/
    Assumes schema created by xmlreader.py. 
    '''
    # Normalize entry for URL
    # Define translation map for nonstandard characters
    character_map = {
        225: 97,  # á --> a
        253: 121,  # ý --> y
        240: 100,  # ð --> d
        250: 117,  # ú --> u
        233: 101,  # é --> e
        243: 111,  # ó --> o
        246: 111,  # ö --> o
        248: 111,  # ø --> o
        237: 105,  # í --> i
        32: 45,    # space --> hyphen
    }

    entry_unnormalized = data["lemma"].lower()
    entry_normalized = entry_unnormalized.translate(character_map)
    entry_normalized = re.sub(r'-$', '', entry_normalized)
    # Take care of ligatures & capitalization separately (transform into two characters)
    # þ --> th
    # æ --> ae
    # œ --> oe
    entry_normalized = entry_normalized.replace("þ", "th").replace("æ", "ae").replace("œ", "oe")

    # Try to access webpage
    url = "https://old-icelandic.vercel.app/word/" + entry_normalized
    response = requests.get(url)
    # Raise an exception if an error occurs (may want to silence this later)
    response.raise_for_status()

    # Extract data from webpage using lxml
    doc = html.fromstring(response.text)

    # Check to make sure lemma matches page header
    page_lemma = doc.xpath(".//dl/dt/strong/text()")[0]
    if page_lemma != data["lemma"]: 
        print(f"Lemma mismatch for initial fetch: data '{data["lemma"]}' vs. page '{page_lemma}'. Querying {url}-2")
        # Try to request second entry for normalized lemma
        response = requests.get(url+"-2")
        response.raise_for_status()
        doc = html.fromstring(response.text)
        page_lemma = doc.xpath(".//dl/dt/strong/text()")[0]
        if page_lemma != data["lemma"]:
            print(f"Second query unsuccessful for lemma {data["lemma"]}. REMEDIATE MANUALLY.")
            return data

    valid_pos_abbr = [  # POS tags found inside <abbr> tag
        "v.", "adv."
    ]
    valid_pos_no_abbr = [  # Valid POS tags not found inside <abbr> tag
        "a. ", "prep. ", "pp. ", "v. refl. "
    ]
    valid_gender = [  # Valid gender tags (found inside <abbr> tag, in lieu of 'noun' POS tag)
        "m.", "f.", "n."
    ]
    # Case 1: entry has <abbr> tag
    for abbr in doc.xpath(".//dl/dd[contains(@class, 'WordDefinition_itemDescription')]/abbr"):
        if abbr.text in valid_pos_abbr:
            data["pos"] = abbr.text
            abbr.drop_tree()
            break
        elif abbr.text in valid_gender: 
            data["pos"] = "n."
            data["gender"] = abbr.text
            abbr.drop_tree()
            break
    # Case 2: POS still not found; search descriptions
    if data["pos"] == "\\N":
        for desc in doc.xpath(".//dl/dd[contains(@class, 'WordDefinition_itemDescription')]"):
            for abbr in valid_pos_no_abbr: 
                if desc.text and abbr in desc.text:
                    data["pos"] = abbr
                    desc.text = re.sub(abbr, '', desc.text, count=1)
                    break

    # Fill in gloss -- select first <i> tag in description tag
    gloss_tags = doc.xpath(".//dl/dd[contains(@class, 'WordDefinition_itemDescription')]/i")
    if gloss_tags:
        data["gloss"] = gloss_tags[0].text

    # Fill in entry_str & entry
    # No need to split into senses -- all missing are 'main' entries
    # N.B. need to manually remediate 'biða' (wants second definition only)
    entry_tags = doc.xpath(".//dl/dd[contains(@class, 'WordDefinition_itemDescription')]")
    entry_texts = [element.text_content() for element in entry_tags]
    entry_full = " | \\n | ".join(entry_texts)
    data["entry_str"] = entry_full.strip()
        
    # Process entry HTML
    entry_html = None
    for et in entry_tags: 
        strip_tags(et, "abbr", "dd")
        if entry_html is not None: 
            entry_html += "\\n"
        else: 
            entry_html = ""
        entry_html += f'<div class="oldnorse bodytext">{html.tostring(et, method="html", encoding="unicode")}</div>'
    data["entry"] = entry_html

    return data


if __name__ == "__main__": 
    #region test-completion
    TEST_ONLY = False
    if TEST_ONLY: 
        test_row = {
                "lemma_id": "4",
                "lemma": "afbrigð",
                "sense_num": "\\N",
                "type": "main",
                "ipa": "[avbriɣð]",
                "pos": "\\N",
                "gender": "\\N",
                "entry": "\\N",
                "entry_str": "\\N",
                "gloss": "\\N",
            }
        
        new_row = scrape_entry(test_row)
        print(new_row)
        import sys
        sys.exit()
    #endregion
    
    #region complete-csv
    csv_data_fixed = []
    fixed_data_only = []
    
    start_time = time()
    rows_fixed = 0
    still_missing = 0
    headers = ["lemma_id","lemma","sense_num","type","ipa","pos","gender","entry","entry_str","gloss"]
    # csv_obj, missing_lemmas = get_missing("zoega.csv", headers)
    with open("zoega.csv", 'r') as f: 
            reader = csv.DictReader(f, headers)
            for row in reader: 
                still_missing += 1
                if row["entry_str"] == "\\N":
                    try:
                        fixed_row = scrape_entry(row)
                        csv_data_fixed.append(fixed_row)
                        fixed_data_only.append(fixed_row)
                        rows_fixed += 1
                        still_missing -= 1
                    except requests.exceptions.HTTPError as err:
                        print("HTTPError:", err)
                        continue
                else: 
                    # Row is already filled out; no need to update
                    csv_data_fixed.append(row)
                    still_missing -= 1

    with open("zoega-fixed.csv", 'w') as f: 
        writer = csv.DictWriter(f, headers)
        writer.writeheader()
        writer.writerows(csv_data_fixed)
    with open("fixed-rows-only.csv", 'w') as f: 
        writer = csv.DictWriter(f, headers)
        writer.writeheader()
        writer.writerows(fixed_data_only)
    print("Total rows fixed:", rows_fixed)
    print("Total missing entries remaining:", still_missing)
    print("Runtime:", time() - start_time)
    #endregion