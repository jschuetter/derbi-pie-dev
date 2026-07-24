# Kaikki Data
This directory contains the **raw Wiktextract data JSONL** based on the 2026-05-01 `enwiktionary` dump available on the Kaikki [Raw Data Downloads](https://kaikki.org/dictionary/rawdata.html) page. There are also two scripts present here for parsing. 

The input data was sourced from [kaikki.org](https://kaikki.org/index.html).
The parser scripts are the original work of [Jacob Schuetter](https://github.com/jschuetter) for the DERBi PIE project.
---
**`jsonlparser.py`** filters the Wiktextract data for entries matching the provided `lang` or `lang_code` parameters. It writes a new JSONL file to this directory named `{lang_code}-lexicon.jsonl` containing the relevant entries, unmodified from their form in the Wiktextract data.

*Required arguments:*
- `lang`: the name of the language in the Wiktextract data
- `lang_code`: the `lang_code` value of the language in the Wiktextract data. Used as a fallback for `lang` and helps determine the name of the output file. 

If you're having trouble finding either value, look up an example entry on the web: https://kaikki.org/dictionary/index.html
---
**`jsonlreader.py`** parses the filtered JSONL data into the DERBi PIE format and writes a CSV file according to the schema used elsewhere in this repository. 

*Required arguments:*
- `input_file`: the path to a JSONL file produced by `jsonlparser.py`. Output will be written to the same path, as a CSV file.

## Languages
Languages that have been parsed based on Wiktextract data so far: 
- Lithuanian
- Old Church Slavonic