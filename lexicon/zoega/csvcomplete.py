'''
csvcomplete.py
A web scraping script to fill in gaps in the Zoega XML
(i.e. missing entries)
'''

import csv

def get_missing(csv_file, csv_headers): 
    '''
    Return a list of (lemma_id, lemma) tuples for 
    all lemmas in the CSV which have blank 'entry_str' fields.
    Lemmas are returned in the order in which they are read. 
    '''
    missing_lemmas = []
    with open(csv_file, 'r') as f: 
        reader = csv.DictReader(f, csv_headers)
        for row in reader: 
            if row["entry_str"] == "\\N":
                missing_lemmas.append((row["lemma_id"], row["lemma"]))
    return missing_lemmas

if __name__ == "__main__": 
    headers = ["lemma_id","lemma","sense_num","type","ipa","pos","gender","entry","entry_str","gloss"]
    missing_lemmas = get_missing("zoega.csv", headers)
    print("Total definitions missing:", len(missing_lemmas))
    