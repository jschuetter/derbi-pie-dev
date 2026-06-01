# Lexicon - Lithuanian
**Enwiktionary Dump**

This directory contains an XML to CSV parserfor the `enwiktionary` data dump from Wiktionary, intended for parsing the Lithuanian lexicon section. 

The input data was sourced from [kaikki.org](https://kaikki.org/index.html).
The parser script is the original work of [Jacob Schuetter](https://github.com/jschuetter) for the DERBi PIE project.


## Input Data Information
The input data for the Lithuanian lexicon was sourced from the **raw Wiktextract data JSONL** based on the 2026-05-01 `enwiktionary` dump available on the Kaikki [Raw Data Downloads](https://kaikki.org/dictionary/rawdata.html) page.
The script `jsonl-parser.py` was written to extract the Lithuanian data from the main JSONL file. The relevant data is stored in this directory as `lithuanian-lexicon.jsonl`. 
Entries are filtered on `"lang" = "Lithuanian"` or `"lang_code" = "lt"`.