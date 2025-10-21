-- Create matching tables
CREATE TABLE reflex_matches (
	lex_ref_link_id INT PRIMARY KEY NOT NULL,
    match_str TEXT -- null allowed - #46314 has null reflex?
);
CREATE TABLE lemma_matches (
	lewis_short_id INT PRIMARY KEY NOT NULL,
    match_str TEXT NOT NULL
);

-- TRUNCATE TABLE reflex_matches;
INSERT INTO reflex_matches
(lex_ref_link_id, match_str, lewis_short_id)
SELECT lex_ref_link_id, reflex, NULL
FROM lex_ref_link
WHERE orig_lang_abbrev LIKE '%lat%';

-- Alter match_str in reflex_matches
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


-- Build lemma_matches table
TRUNCATE TABLE lemma_matches;
INSERT INTO lemma_matches
(lewis_short_id, match_str)
SELECT id, REGEXP_REPLACE(REPLACE(REPLACE(lemma, 'v', 'u'), 'j', 'i'), '[0-9]', '')  # Replace v/u, j/i, and numerals
FROM lewis_short;

-- New approach: create new table to match reflexes to lemmas
CREATE TABLE reflex_lemma_link (
	id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
    lex_ref_link_id INT NOT NULL,
    match_str TEXT,
    lewis_short_id INT
);

-- TRUNCATE TABLE reflex_lemma_link;
-- Build mapping table in blocks (10k IDs/1k entries each) to avoid SQL server timeout
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

-- Delete query if need to undo something above
SET SQL_SAFE_UPDATES = 0;
DELETE FROM reflex_lemma_link
WHERE lex_ref_link_id >= 50000;
SET SQL_SAFE_UPDATES = 1;

-- Import lemmatized doc from CLTK, update reflex_matches
CREATE TABLE reflex_lemmatized (
	id INT PRIMARY KEY AUTO_INCREMENT,
    match_str TEXT,
    lemmatized TEXT,
    lewis_short_id INT
);
-- Load data from CSV
TRUNCATE TABLE reflex_lemmatized;
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/null_reflexes_matched.csv'
INTO TABLE reflex_lemmatized
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(match_str, lemmatized);
-- Map lemmas to lewis & short
SET SQL_SAFE_UPDATES = 0;
UPDATE reflex_lemmatized rl
LEFT JOIN lemma_matches lm
ON rl.lemmatized = lm.match_str
SET rl.lewis_short_id = lm.lewis_short_id
WHERE rl.id < 500;
SET SQL_SAFE_UPDATES = 1;
-- N.B. NEEDED TO REVIEW LEMMATIZATION - some incorrect
-- Write matched lemmas to reflex_lemma_link
UPDATE reflex_lemma_link rll
LEFT JOIN reflex_lemmatized rlm
ON rll.match_str = rlm.match_str
SET rll.lewis_short_id = rlm.lewis_short_id
WHERE rlm.lewis_short_id IS NOT NULL;