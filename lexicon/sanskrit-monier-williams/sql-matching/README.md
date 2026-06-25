# Sanskrit SQL Matching
This directory contains output from `~/MySQL/sanskrit/skMatching.sql`, exported in CSV format. A description of each file is below.

- `skt_exact_matches.csv`: entries where both lemma and entry_str matched (accent- and case-sensitive) (*automatically approved, with the exception of duplicates which need remediation, separated in 2 tables below*)
    - `skt_approved_matches.csv`: all "exact-match" entries, with duplicates removed
    - `skt_duplicate_matches.csv`: all duplicates from `skt_exact_matches.csv`
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
