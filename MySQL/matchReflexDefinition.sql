SELECT * FROM lewis_short;
SELECT * FROM lex_ref_link;

# Match latin lex_ref entries to lewis_short entries
SELECT ref.lex_ref_link_id, ref.orig_lang_abbrev, ref.reflex, ls.id, ls.lemma, ls.entry
FROM lex_ref_link ref
JOIN lewis_short ls 
-- ON ref.reflex = ls.lemma
ON REPLACE(
	REPLACE(
		REPLACE(ref.reflex, 'v', 'u'),
			'j', 'i'),
				'-', '') 
	= REPLACE(
		REPLACE(ls.lemma, 'v', 'u'),
			'j', 'i')
OR REPLACE(
	REPLACE(
		REPLACE(ref.reflex, 'v', 'u'),
			'j', 'i'),
				'-', '') 
	LIKE CONCAT(
		REPLACE(
			REPLACE(ls.lemma, 'v', 'u'),
				'j', 'i'), ',%')
WHERE ref.orig_lang_abbrev LIKE '%lat%';

# Count matches - query timeout
SELECT COUNT(*)
FROM lex_ref_link ref
JOIN lewis_short ls 
-- ON ref.reflex = ls.lemma
ON REPLACE(
	REPLACE(
		REPLACE(ref.reflex, 'v', 'u'),
			'j', 'i'),
				'-', '') 
	= REPLACE(
		REPLACE(ls.lemma, 'v', 'u'),
			'j', 'i')
OR REPLACE(
	REPLACE(
		REPLACE(ref.reflex, 'v', 'u'),
			'j', 'i'),
				'-', '') 
	LIKE CONCAT(
		REPLACE(
			REPLACE(ls.lemma, 'v', 'u'),
				'j', 'i'), ',%')
WHERE ref.orig_lang_abbrev LIKE '%lat%';

# Counted 

# Find total # of latin entries in lex_ref_link
SELECT COUNT(*)
FROM lex_ref_link
WHERE orig_lang_abbrev LIKE '%lat%';
# 5419 total Latin entries

SELECT COUNT(*) FROM lewis_short;
# 51636 entries in Lewis & Short


# Create matching table
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

# Alter match_str
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
'(\\w+)');
SET SQL_SAFE_UPDATES = 1;
SELECT * FROM reflex_matches;

TRUNCATE TABLE lemma_matches;
INSERT INTO lemma_matches
(lewis_short_id, match_str)
SELECT id, REGEXP_REPLACE(REPLACE(REPLACE(lemma, 'v', 'u'), 'j', 'i'), '[0-9]', '')
FROM lewis_short;

# Match Lewis & Short IDs to reflexes
SELECT COUNT(*) FROM reflex_matches; # 5419 total - update 1k at a time?
SET SQL_SAFE_UPDATES = 0;
UPDATE reflex_matches ref
JOIN lemma_matches ls 
ON ref.match_str = ls.match_str
	OR ref.match_str LIKE CONCAT(ls.match_str, ',%')
SET ref.lewis_short_id = ls.lewis_short_id
WHERE ref.lex_ref_link_id < 100;
-- WHERE ref.lex_ref_link_id >= 500 AND ref.lex_ref_link_id < 1000
SET SQL_SAFE_UPDATES = 1;

SELECT ref.lex_ref_link_id, ref.match_str, ref.lewis_short_id, ls.id, ls.lemma
FROM reflex_matches ref
JOIN lewis_short ls 
ON ref.match_str = REPLACE(REPLACE(ls.lemma, 'v', 'u'), 'j', 'i')
	OR ref.match_str LIKE CONCAT(REPLACE(REPLACE(ls.lemma, 'v', 'u'), 'j', 'i'), ',%');

SELECT REGEXP_SUBSTR(reflex, '^(\\w+)')
FROM lex_ref_link
WHERE orig_lang_abbrev LIKE '%lat%';


# New approach: create new table
CREATE TABLE reflex_lemma_link (
	id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
    lex_ref_link_id INT NOT NULL,
    match_str TEXT,
    lewis_short_id int
);
ALTER TABLE reflex_lemma_link ADD COLUMN id INT NOT NULL;
ALTER TABLE reflex_lemma_link ADD PRIMARY KEY (id);
ALTER TABLE reflex_lemma_link DROP PRIMARY KEY;
ALTER TABLE reflex_lemma_link MODIFY COLUMN id INT NOT NULL AUTO_INCREMENT;
ALTER TABLE reflex_lemma_link DROP COLUMN id;

TRUNCATE TABLE reflex_lemma_link;
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
ORDER BY rf.lex_ref_link_id
LIMIT 1000;

SET SQL_SAFE_UPDATES = 0;
DELETE FROM reflex_lemma_link
WHERE lex_ref_link_id >= 50000;
SET SQL_SAFE_UPDATES = 1;

# Handle emtpy cells - currently 
# Lemmas with multiple Lewis & Short entries (i.e. lemmas suffixed with '1' or '2')
# Now handled in creating lemma_matches table
UPDATE reflex_lemma_link rl
JOIN lemma_matches lm
ON rl.match_str = lm.match_str
SET rl.lewis_short_id = lm.lewis_short_id
WHERE rl.lewis_short_id IS NULL
AND rl.lex_ref_link_id > 10000;
# Now 973 null entries

# Entries of other principal parts (infinitives or perfect forms)
# FAILED DON'T DO THIS
CREATE TABLE reflex_lemma_link_orth (
	id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
    lex_ref_link_id INT NOT NULL,
    match_str TEXT,
    lewis_short_id int
);
INSERT INTO reflex_lemma_link_orth
(lex_ref_link_id, match_str, lewis_short_id)
SELECT rl.lex_ref_link_id, rl.match_str, ls.id
FROM reflex_lemma_link rl
JOIN lewis_short ls
ON ls.orthography LIKE CONCAT('%', rl.match_str, '%')
WHERE rl.lewis_short_id IS NULL;
