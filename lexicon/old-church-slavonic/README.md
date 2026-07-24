# Lexicon - Old Church Slavonic
**Enwiktionary Dump**

This directory contains an JSONL to CSV parser (`jsonlreader.py`) for the `enwiktionary` data dump from Wiktionary, intended for parsing the Lithuanian lexicon section. See "Input Data Information" below for details on the input data. The output is stored in this directory as `old-church-slavonic.csv`.

The input data was sourced from [kaikki.org](https://kaikki.org/index.html).
The parser script is the original work of [Jacob Schuetter](https://github.com/jschuetter) for the DERBi PIE project.


## Input Data Information
The input data for the Lithuanian lexicon was sourced from the **raw Wiktextract data JSONL** based on the 2026-05-01 `enwiktionary` dump available on the Kaikki [Raw Data Downloads](https://kaikki.org/dictionary/rawdata.html) page.
The script `jsonl-parser.py` was written to extract the Lithuanian data from the main JSONL file. The relevant data is stored in this directory as `ocs-lexicon.jsonl`. 
Entries are filtered on `"lang" = "Old Church Slavonic"` or `"lang_code" = "cu"`.