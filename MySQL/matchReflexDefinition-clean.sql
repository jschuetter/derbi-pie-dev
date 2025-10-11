# Create matching tables
CREATE TABLE reflex_matches (
	lex_ref_link_id INT PRIMARY KEY NOT NULL,
    match_str TEXT # null allowed - #46314 has null reflex?
);
CREATE TABLE lemma_matches (
	lewis_short_id INT PRIMARY KEY NOT NULL,
    match_str TEXT NOT NULL
);

TRUNCATE TABLE reflex_matches;
INSERT INTO reflex_matches
(lex_ref_link_id, match_str, lewis_short_id)
SELECT lex_ref_link_id, reflex, NULL
FROM lex_ref_link
WHERE orig_lang_abbrev LIKE '%lat%';

# Alter match_str in reflex_matches
SELECT * FROM (
SELECT REGEXP_SUBSTR(REGEXP_REPLACE(match_str, '[-()*]', ''), '(\\w+)') AS col1, match_str, lex_ref_link_id FROM reflex_matches 
) AS innertable
WHERE col1 IS NULL;
SELECT lex_ref_link_id, match_str FROM reflex_matches WHERE match_str LIKE '%NAME%';

SET SQL_SAFE_UPDATES = 0;
UPDATE reflex_matches
SET match_str = REGEXP_SUBSTR(
	REGEXP_REPLACE(
		REPLACE(
			REPLACE(match_str, 'v', 'u'),
		'j', 'i'),
	'[-()*]', ''),
'(\\w+)');  # Replace v/u, j/i, punctuation, and take first word only
SET SQL_SAFE_UPDATES = 1;
SELECT * FROM reflex_matches;


# Build lemma_matches table
TRUNCATE TABLE lemma_matches;
INSERT INTO lemma_matches
(lewis_short_id, match_str)
SELECT id, REGEXP_REPLACE(REPLACE(REPLACE(lemma, 'v', 'u'), 'j', 'i'), '[0-9]', '')  # Replace v/u, j/i, and numerals
FROM lewis_short;

# New approach: create new table to match reflexes to lemmas
CREATE TABLE reflex_lemma_link (
	id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
    lex_ref_link_id INT NOT NULL,
    match_str TEXT,
    lewis_short_id INT
);

TRUNCATE TABLE reflex_lemma_link;
# Build mapping table in blocks (10k IDs/1k entries each) to avoid SQL server timeout
INSERT INTO reflex_lemma_link
(lex_ref_link_id, match_str, lewis_short_id)
SELECT rf.lex_ref_link_id, rf.match_str, ls.lewis_short_id
FROM reflex_matches rf
LEFT JOIN lemma_matches ls
ON rf.match_str = ls.match_str
OR rf.match_str LIKE CONCAT(ls.match_str, ',%')
-- WHERE rf.lex_ref_link_id < 1000
-- WHERE rf.lex_ref_link_id >= 90000 AND rf.lex_ref_link_id < 100000
WHERE rf.lex_ref_link_id > 100000
ORDER BY rf.lex_ref_link_id;
-- LIMIT 1000;

# Delete query if need to undo something above
SET SQL_SAFE_UPDATES = 0;
DELETE FROM reflex_lemma_link
WHERE lex_ref_link_id >= 50000;
SET SQL_SAFE_UPDATES = 1;

# Handle emtpy cells - currently 
# Lemmas with multiple Lewis & Short entries (i.e. lemmas suffixed with '1' or '2')
# Now handled in creating lemma_matches table
-- UPDATE reflex_lemma_link rl
-- JOIN lemma_matches lm
-- ON rl.match_str = lm.match_str
-- SET rl.lewis_short_id = lm.lewis_short_id
-- WHERE rl.lewis_short_id IS NULL
-- AND rl.lex_ref_link_id > 10000;
# Now 973 null entries

# Entries of other principal parts (infinitives or perfect forms)
# FAILED DON'T DO THIS
-- CREATE TABLE reflex_lemma_link_orth (
-- 	id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
--     lex_ref_link_id INT NOT NULL,
--     match_str TEXT,
--     lewis_short_id int
-- );
-- INSERT INTO reflex_lemma_link_orth
-- (lex_ref_link_id, match_str, lewis_short_id)
-- SELECT rl.lex_ref_link_id, rl.match_str, ls.id
-- FROM reflex_lemma_link rl
-- JOIN lewis_short ls
-- ON ls.orthography LIKE CONCAT('%', rl.match_str, '%')
-- WHERE rl.lewis_short_id IS NULL;
