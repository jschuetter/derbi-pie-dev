-- Create matching tables
CREATE TABLE reflex_matches (
	lex_ref_link_id INT PRIMARY KEY NOT NULL,
    match_str TEXT -- null allowed - #46314 has null reflex?
);
CREATE TABLE lemma_matches (
	lex_master_id INT PRIMARY KEY NOT NULL,
    match_str TEXT NOT NULL
);

TRUNCATE TABLE reflex_matches;
INSERT INTO reflex_matches
(lex_ref_link_id, match_str, lewis_short_id)
SELECT lex_ref_link_id, reflex, NULL
FROM lex_ref_link
WHERE orig_lang_abbrev LIKE '%lat%';

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
(lex_master_id, match_str)
SELECT lemma_id, REGEXP_REPLACE(REPLACE(REPLACE(lemma, 'v', 'u'), 'j', 'i'), '[0-9]', '')  # Replace v/u, j/i, and numerals
FROM lex_master;

SELECT * FROM lemma_matches;

-- New approach: create new table to match reflexes to lemmas
DROP TABLE reflex_lemma_link;
CREATE TABLE reflex_lemma_link (
	id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
    match_str TEXT NOT NULL,
    lex_ref_link_id INT NOT NULL,
    lex_ref_gloss TEXT,
    lex_master_id INT,
    lex_master_gloss TEXT
);

TRUNCATE TABLE reflex_lemma_link;
-- Build mapping table in blocks (10k IDs/1k entries each) to avoid SQL server timeout
INSERT INTO reflex_lemma_link
(lex_ref_link_id, match_str, lex_master_id)
SELECT rf.lex_ref_link_id, rf.match_str, lm.lex_master_id
FROM reflex_matches rf
LEFT JOIN lemma_matches lm
ON rf.match_str = lm.match_str;
-- OR rf.match_str LIKE CONCAT(lm.match_str, ',%');
-- WHERE rf.lex_ref_link_id < 1000
-- WHERE rf.lex_ref_link_id >= 90000 AND rf.lex_ref_link_id < 100000
-- WHERE rf.lex_ref_link_id > 100000
-- ORDER BY rf.lex_ref_link_id;
-- LIMIT 1000;

SELECT * FROM reflex_lemma_link WHERE lex_master_id IS NULL;

-- Delete query if need to undo something above
SET SQL_SAFE_UPDATES = 0;
DELETE FROM reflex_lemma_link
WHERE lex_ref_link_id >= 50000;
SET SQL_SAFE_UPDATES = 1;

-- Sync up Andrew's work
DELETE FROM reflex_lemma_link
WHERE lex_ref_link_id IN (593, 2363, 14936, 16238);
DELETE FROM lex_ref_link
WHERE lex_ref_link_id IN (593, 2363, 14936, 16238);

DROP TABLE reflex_lemmatized;
CREATE TABLE reflex_lemmatized (
	lex_ref_link_id INT PRIMARY KEY,
    match_str TEXT,
    lemmatized TEXT,
    lex_master_id INT
);
-- Load data from CSV
TRUNCATE TABLE reflex_lemmatized;
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/matched-reflexes.csv'
INTO TABLE reflex_lemmatized
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(lex_ref_link_id, match_str, @extra, @gloss, @comments, lemmatized);
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/more_null_reflexes.csv'
INTO TABLE reflex_lemmatized
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(@id, match_str, lex_ref_link_id, lemmatized);

SELECT * FROM reflex_lemmatized 
WHERE lex_ref_link_id IN (10176, 10180, 8877, 54351, 57137, 2257, 33885, 34238, 1244, 54352, 60423, 79788, 2790, 10212, 37157, 45683, 50158, 51624, 65011, 2171, 14419, 14809, 16633, 17147, 33266, 52580, 62205, 65008, 75099, 15041, 15887, 20674, 30982, 37077, 79720, 84780, 1048, 1079, 5825, 9991, 10267, 21494, 21555, 28627, 37076, 53509, 55098, 79962, 454, 17068, 69378, 13014, 16208, 16631, 20092, 60398, 61182, 73989, 83555, 2361, 6213, 6506, 6517, 8942, 9990, 20554, 33917, 67690, 85151, 615, 5178, 34602, 37075, 2049, 2053, 2323, 2494, 3720, 3958, 8694, 8926, 10693, 10694, 11279, 11833, 14810, 31389, 31390, 33883, 37073, 40703, 53753, 2287, 5097, 5264, 5265, 10173, 13496, 16632, 47619, 51418, 8582, 10177, 10182, 19461, 20551);

DELETE FROM reflex_lemmatized
WHERE lex_ref_link_id in (13014, 20092, 51624);
DELETE FROM reflex_lemmatized
WHERE lex_ref_link_id IN (593, 2363, 14936, 16238);

-- Normalize lemmas
UPDATE reflex_lemmatized
SET lemmatized = RTRIM(REGEXP_REPLACE(REPLACE(REPLACE(lemmatized, 'v', 'u'), 'j', 'i'), '[0-9]', ''));  # Replace v/u, j/i, and numerals, trim spaces

-- Map lemmas to lewis & short
SET SQL_SAFE_UPDATES = 0;
UPDATE reflex_lemmatized rl
LEFT JOIN lemma_matches lm
ON rl.lemmatized = lm.match_str
SET rl.lex_master_id = lm.lex_master_id;
SET SQL_SAFE_UPDATES = 1;

SELECT * FROM reflex_lemmatized; -- WHERE lex_master_id IS NOT NULL;

-- Update reflex_lemma_link
UPDATE reflex_lemma_link rll
LEFT JOIN reflex_lemmatized rlm
ON rll.match_str = rlm.match_str
SET rll.lex_master_id = rlm.lex_master_id
WHERE rlm.lex_master_id IS NOT NULL;

SELECT * FROM reflex_lemma_link WHERE lex_master_id IS NULL;

-- Write to lex_ref_link
UPDATE lex_ref_link lrl
JOIN reflex_lemma_link rll
ON rll.lex_ref_link_id = lrl.lex_ref_link_id
SET lrl.word_id = rll.lex_master_id
WHERE rll.lex_master_id IS NOT NULL;

SELECT COUNT(*) FROM reflex_lemma_link;