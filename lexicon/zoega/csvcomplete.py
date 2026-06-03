'''
csvcomplete.py
A web scraping script to fill in gaps in the Zoega XML
(i.e. missing entries)
'''

import csv, requests, re
from lxml import html
from time import time

from remove_tag import remove_tag

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
    response = requests.get("https://old-icelandic.vercel.app/word/" + entry_normalized)
    # Raise an exception if an error occurs (may want to silence this later)
    response.raise_for_status()

    # Extract data from webpage using lxml
    doc = html.fromstring(response.text)

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
            remove_tag(abbr)
            break
        elif abbr.text in valid_gender: 
            data["pos"] = "n."
            data["gender"] = abbr.text
            remove_tag(abbr)
            break
    # Case 2: POS still not found; search descriptions
    if data["pos"] == "\\N":
        for desc in doc.xpath(".//dl/dd[contains(@class, 'WordDefinition_itemDescription')]"):
            for abbr in valid_pos_no_abbr: 
                if abbr in desc.text:
                    data["pos"] == abbr
                    desc.text = re.sub(abbr, '', desc.text, count=1)
                    break

    # Fill in gloss -- select first <i> tag in description tag
    gloss_tags = doc.xpath(".//dl/dd[contains(@class, 'WordDefinition_itemDescription')]/i")
    if gloss_tags:
        data["gloss"] = gloss_tags[0].text

    # Fill in entry_str & entry
    entry_tags = doc.xpath(".//dl/dd[contains(@class, 'WordDefinition_itemDescription')]")
    entry_texts = []
    for element in entry_tags: 
        entry_texts.append("".join(element.itertext()))
    entry_full = " | \\n | ".join(entry_texts)
    # TODO: Split entry into senses
        
    data["entry_str"] = entry_full
    return data
    # data["entry"] = ""


if __name__ == "__main__": 
    #region test-completion
    test_row = {
            "lemma_id": "4",
            "lemma": "abbindi",
            "sense_num": "\\N",
            "type": "main",
            "ipa": "[abːindi]",
            "pos": "\\N",
            "gender": "\\N",
            "entry": "\\N",
            "entry_str": "\\N",
            "gloss": "\\N",
        }
    
    new_row = scrape_entry(test_row)
    print(new_row)


    #endregion
    
    #region complete-csv
    # test_fixed_data = []
    
    # start_time = time()
    # rows_fixed = 0
    # still_missing = 0
    # headers = ["lemma_id","lemma","sense_num","type","ipa","pos","gender","entry","entry_str","gloss"]
    # # csv_obj, missing_lemmas = get_missing("zoega.csv", headers)
    # with open("zoega.csv", 'r') as f: 
    #         reader = csv.DictReader(f, headers)
    #         for row in reader: 
    #             if row["entry_str"] == "\\N":
    #                 try:
    #                     test_fixed_data.append(scrape_entry(row))
    #                     rows_fixed += 1
    #                 except requests.exceptions.HTTPError as err:
    #                     print("HTTPError:", err)
    #                     continue

    # with open("test-fixed.csv", 'w') as f: 
    #     writer = csv.DictWriter(f, headers)
    #     writer.writeheader()
    #     writer.writerows(test_fixed_data)
    # print("Total rows fixed:", rows_fixed)
    # print("Total missing entries remaining:", still_missing)
    # print("Runtime:", time() - start_time)
    #endregion