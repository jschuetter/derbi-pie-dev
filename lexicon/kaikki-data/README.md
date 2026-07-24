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
- Old Irish

## Import Process
1) Extract and parse relevant data from `enwiktionary` dump using `kaikki_importer.py`.
2) Import data to MySQL using `~/MySQL/importLang.sql`.
    - ==**Be sure to set the appropriate `@lang_code` and import `.csv` path!!**==
3) Retrieve literal reflex matches from `lex_ref_link` using `~/MySQL/getLiteralMatches.sql`.
4) Review matches using helper scripts in `~/lexicon/matching/`
    1) Split returned matches into *unique* and *duplicate* matches using `~/lexicon/matching/split_matches.py`.
    2) Review proposed matches using `resolve_single_manual.py` (for unique matches) and `resolve_multiple_manual.py` (for duplicate matches).
5) Update `lex_ref_link` with approved matches using `~/MySQL/addMatches.sql`.