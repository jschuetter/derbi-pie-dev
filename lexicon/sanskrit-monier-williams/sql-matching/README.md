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
