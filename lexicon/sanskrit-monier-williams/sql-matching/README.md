# Sanskrit SQL Matching
This directory contains output from `~/MySQL/sanskrit/skMatching.sql`, exported in CSV format. A description of each file is below.

- `skt_exact_matches.csv`: entries where both lemma and entry_str matched (accent- and case-sensitive) (*automatically approved, with the exception of duplicates which need remediation, separated in 2 tables below*)
    - `skt_approved_matches.csv`: all "exact-match" entries, with duplicates removed
    - `skt_duplicate_matches.csv`: all duplicates from `skt_exact_matches.csv` (72 entries -- **REMEDIATE MANUALLY**)
- `skt_single_matches.csv`: all parsed entries that matched a single lemma in `lex_master` which was *not yet paired* with a `parsed_id` in `skt_exact_matches.csv`.  (*need review/refinement, but likely approved - often due to transliteration issues*)
- `skt_repeat_matches.csv`: parsed entries that matched a single lemma in `lex_master` which was already paired with another `parsed_id`. (*usually new lemmas split from other entries*)
- `skt_multiple_matches.csv`: parsed entries that matched multiple entries in `lex_master`. `lex_master` entries may or may not have already been paired, as noted by the `master_lemma_paired` column. (*manual review - may be new lemmas or match with now-split entry*)
- `skt_no_matches.csv`: parsed entries for which no match could be found in `lex_master`. (*likely completely new entries -- e.g. derived forms*)


*Total entries in each after running `sktMatching.sql`:*
exact | single | repeat | multiple | unmatched
168108 | 36108 | 24207 | 19419 | 808
===
total | approved | duplicates | remaining
238179 | 168036 | 72 | 70097

# New match files
This directory now also contains new match files generated using Python, based on the above CSV files. *These files may have varying schemas, so be sure to check when importing back into MySQL.* File descriptions are below. To save space in the GH repo, output CSV files have been backed up to OneDrive.

- Resolution scripts (*in parent directory*)
    - `resolve_single_auto.py`, `resolve_single_manual.py`: scripts for resolving `skt_single_matches.csv` (first by auto-matching as many lemmas as possible, then by manually reviewing good candidate matches, as determined by Levenshtein distance)
        - This same script was also used for `skt_repeat_matches.csv`
    - `resolve_manual_auto.py`, `resolve_multiple_manual.py`: same as above, for `skt_multiple_matches.csv`. Groups rows by `parsed_id` and chooses the best match for each group. 
- Output directories
    - `/approved/`: matches approved for entry into MySQL
    - `/archive/`: temporary or in-progress output files that are no longer needed (contents have been copied/split into other files)
    - `/need-remediation/`: match results that need manual remediation. This may mean that multiple `parsed_id`s are mapped to the same `master_id`, or that the `master_id`s assigned in that file were already matched elsewhere, or that the `parsed_id`s present did not match any `master_id` and need to be assigned a new `lex_master_id`.
    - `/rejected/`: match results that have been outright rejected (just for archive purposes) 

# SQL scripts reference
(See directory `~/MySQL/sanskrit`)

- `importSkMatches.sql`
- `reindex_skt.sql`
- `skMatching.sql`
- `skMatching2.sql`: a near-copy of `skMatching` experimenting with other match techniques. Not used in final pipeline.
- `skt_update_master.sql`: script for updating `lex_master` schema and values after matching & reindexing
- `updateLexMaster.sql`: an old script for importing matches from CSV into `lex_senses` (`lex_master` never implemented)


## Matching Pipeline
1) Py: Parse XML (`~/lexicon/sanskrit-monier-williams/xmlparser.py`)
2) SQL: match lemmas & branch out into match types (exact, duplicates, etc.) (`~/MySQL/sanskrit/skMatching.sql`)
3) Py: process match data from SQL
    - Exact/approved matches: no further processing
    - Single matches: `resolve_single_auto.py`, then `resolve_single_manual.py`
    - Repeat/duplicate matches: same pipeline as above, then visual check/remediation of repeat assignments
    - Multiple matches: `resolve_multiple_auto.py`, then `resolve_multiple_manual.py`
    - Unmatched rows: set aside for new-index assignment
4) SQL: import matches from Python & continue processing (`~/MySQL/sanskrit/importSkMatches.sql`)
    1) Create new tables for approved matches, duplicates, and temp table for importing *(once)*
    2) Load data from .csv produced by (3) into temp table
    3) Check for duplicate assignments in `skt_approved_matches` - manually remediate when necessary (update temp table + CSV for later reference)
    4) Add new approved matches to `skt_approved_matches`
    5) Repeat (2) - (4) for each .csv produced by step 3
    6) Query `lex_master` for lemmas that have not been assigned a `parsed_id` match. 
        1) Retrieve all possible matches from `temp_skt_joined`
        2) Pass matches to Python scripts in step (3) above for processing (`resolve_multiple_auto.py` & `resolve_multiple_manual.py`). Retrieve new CSVs of approved matches & confirm lemmas set aside for new-indexing
        3) Repeat steps (2)-(4) for (hopefully) new approved matches
5) SQL: reindex entries (`~/MySQL/sanskrit/reindex_skt.sql`)
    - Create reference/matching table from 'approved matches' containing only (`parsed_id`, `master_id`) pairs
    - Create new, reindexed master & sense tables using **parsed** entry rows & **original, `lex_master`** IDs
6) SQL: update `lex_master` schema to accommodate changes for Sanskrit
    - `ADD COLUMN related INT DEFAULT NULL`
    - `MODIFY COLUMN gender VARCHAR(64)`
7) SQL: drop `lex_master` entries that are now treated as senses
    - *FOREIGN KEY constraints not possible - `lex_master` and `lex_ref_link` under different encodings*
    1) Resolve dropped IDs to appropriate parent entry *(most 'dropped' entries are demoted to senses => point links to new 'master' entry)*
        - Query `lex_master` ID to be dropped in `lex_ref_link`; update all instances to point to new 'master' entry BEFORE dropping `lex_master` entry
8) SQL: Overwrite `lang='Skt.'` entries in `lex_master` and `lex_senses` with reindexed entries from `temp_skt_reindexed_main` and `temp_skt_reindexed_senses`

***Add'l note:*** Also (may) update parsed entries where `gender` listed as `mfn.` -- usually adjectives, rather than nouns
- Some may have differing endings in f. Regexp: `,mf(\(.*?\))?n\.,`