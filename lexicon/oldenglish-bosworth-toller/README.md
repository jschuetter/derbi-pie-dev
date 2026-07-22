# Lexicon - Old English
***An Anglo-Saxon Dictionary* (Bosworth & Toller)**

This directory contains an XML to CSV parser (`xmlreader.py`) and its corresponding input file (`bosworth-toller-1989.xml`) and output (`bosworth-toller.csv`) for the 1989 edition of Bosworth and Toller's *An Anglo-Saxon Dictionary*.

The [original text file](https://www.germanic-lexicon-project.org/txt/oe_bosworthtoller.txt) (`oe_bosworthtoller.txt`) was sourced from the [Germanic Lexicon Project](https://germanic-lexicon-project.org/texts/oe_bosworthtoller_about.html)' and contains two separate works by Bosworth and Toller, the former from 1989 (here called `bosworth-toller-1989`) and the latter supplement, in the 1921 first edition (here called `toller-supplement-1921`). See the `<INTRODUCTION>` in `oe_bosworthtoller.txt` for more detail.
The parser script is the original work of [Jacob Schuetter](https://github.com/jschuetter) for the DERBi PIE project.

## Notes
A list of abbreviations used in Bosworth and Toller can be found in `oebt_abbreviations.xml` ([source](https://www.germanic-lexicon-project.org/xml/oe_bosworthtoller/oebt_abbreviations.xml)).

## Output adjustments
A number of entries in the initial parser output, `bosworth-toller.csv`, had to be manually remediated. See the header comment in `xmlreader.py` for a list of repairs which still need to be made to the parser, if it is going to be used in the future. 
The remediated version of the CSV is titled `bosworth-toller-remediated.csv`. See `updated_ids.txt` for a list of `lemma_id`s and `sense_id`s that were deleted or reinserted in the process.
This is distinct from the **final source-of-truth** version `bosworth-toller-renumbered.csv` in that the master entries in the latter file have `sense_num` values according to the index of duplicates in `lex_master` rather than the list delimiter for display on the page, as the `sense` entries have.

These entries are loaded into `lex_master` using `MySQL/oldenglish/importOE.sql`.