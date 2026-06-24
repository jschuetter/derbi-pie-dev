-- Load Skt. lex_master entries into temp table
DROP TABLE IF EXISTS temp_skt_lex_master;
CREATE TABLE temp_skt_lex_master AS
SELECT * FROM lex_master WHERE lang = 'Skt.';
-- SELECT * FROM temp_skt_lex_master;
DESCRIBE temp_skt_lex_master;

-- Load parsed CSV entries into temp table
DROP TABLE IF EXISTS temp_stg;
CREATE TABLE temp_stg LIKE lex_master;
ALTER TABLE temp_stg MODIFY COLUMN lemma_id VARCHAR(16);
ALTER TABLE temp_stg MODIFY COLUMN gender VARCHAR(29);
ALTER TABLE temp_stg DROP PRIMARY KEY;
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/monier-williams-tempidx.csv'
INTO TABLE temp_stg
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(lemma_id,lemma,lemma_normalized,lemma_translit,sense_num,page_num,`type`,orthography,pos,gender,etymology,entry,entry_str,components,gloss,@related,@sense_id,@h_num,@parent_h_num);

-- Retrieve only 'main' entries from CSV
DROP TABLE IF EXISTS temp_skt_parsed;
CREATE TABLE temp_skt_parsed AS
SELECT * FROM temp_stg WHERE `type` = 'main';
ALTER TABLE temp_skt_parsed ADD PRIMARY KEY (lemma_id, lang);
DROP TABLE temp_stg;

-- Create table with pre-processed join
DROP TABLE IF EXISTS temp_skt_joined;
CREATE TABLE temp_skt_joined AS
SELECT 
	csv.lemma_id AS parsed_id,
	lm.lemma_id AS master_id,
	csv.lemma_translit AS parsed_lemma,
	LEFT(lm.lemma, LOCATE(' (', lm.lemma) - 1) AS master_lemma_trim,
	csv.entry_str AS parsed_entry_str,
	lm.entry_str AS master_entry_str
FROM temp_skt_parsed csv
LEFT JOIN temp_skt_lex_master lm
ON LEFT(lm.lemma, LOCATE(' (', lm.lemma) - 1) COLLATE utf8mb4_0900_as_cs = csv.lemma_translit COLLATE utf8mb4_0900_as_cs
AND csv.page_num = lm.page_num;

-- Select all rows
SELECT * FROM temp_skt_joined ORDER BY CAST(REPLACE(parsed_id, '*', '') AS UNSIGNED), master_id;

-- Select IDs with multiple matches
SELECT parsed_id, COUNT(*) FROM temp_skt_joined GROUP BY parsed_id HAVING COUNT(*) > 1;

-- Matching time!

-- Create tables to store matches
DROP TABLE IF EXISTS skt_exact_matches, skt_repeat_matches, skt_single_matches, skt_multiple_matches, skt_no_matches, skt_lemma_match;
CREATE TABLE skt_exact_matches LIKE temp_skt_joined;
CREATE TABLE skt_repeat_matches LIKE skt_exact_matches;
CREATE TABLE skt_single_matches LIKE skt_exact_matches;
CREATE TABLE skt_multiple_matches LIKE skt_exact_matches;
ALTER TABLE skt_multiple_matches ADD COLUMN master_lemma_paired BOOLEAN;
-- Query entries with no match
CREATE TABLE skt_no_matches AS 
SELECT parsed_id, parsed_lemma, parsed_entry_str 
FROM temp_skt_joined WHERE master_id IS NULL;

-- Function returns True if provided row in skt_lemma_match can be auto-approved as an exact match
DROP FUNCTION IF EXISTS exact_match;
DELIMITER //
CREATE FUNCTION exact_match(parsed_entry_str MEDIUMTEXT, master_entry_str MEDIUMTEXT)
RETURNS BOOLEAN
DETERMINISTIC
NO SQL
BEGIN
	DECLARE parsed_entry_normalized MEDIUMTEXT;
    DECLARE master_entry_normalized MEDIUMTEXT;
    
    SET parsed_entry_normalized = REGEXP_REPLACE(parsed_entry_str, ' +', ' ') COLLATE utf8mb4_0900_as_cs;
    SET master_entry_normalized = REGEXP_REPLACE(master_entry_str, '^[0-9]+\.[ ]+?', '') COLLATE utf8mb4_0900_as_cs;
    RETURN parsed_entry_normalized = master_entry_normalized;
END//
DELIMITER ;

-- Populate exact matches
TRUNCATE TABLE skt_exact_matches;
INSERT INTO skt_exact_matches
SELECT parsed_id, master_id, parsed_lemma, master_lemma_trim, parsed_entry_str, master_entry_str
FROM temp_skt_joined
WHERE exact_match(parsed_entry_str, master_entry_str) = TRUE;
-- SELECT * FROM skt_exact_matches ORDER BY CAST(REPLACE(parsed_id, '*', '') AS UNSIGNED), master_id;
-- SELECT * FROM skt_duplicate_exact_matches;

-- Populate multiple matches
TRUNCATE TABLE skt_multiple_matches;
INSERT INTO skt_multiple_matches
SELECT parsed_id, master_id, parsed_lemma, master_lemma_trim, parsed_entry_str, master_entry_str, FALSE
FROM temp_skt_joined t
WHERE parsed_id NOT IN (
	SELECT DISTINCT parsed_id FROM skt_exact_matches
) AND master_id NOT IN (
	SELECT DISTINCT master_id FROM skt_exact_matches
) AND parsed_id IN (
	SELECT parsed_id FROM temp_skt_joined
    GROUP BY parsed_id HAVING COUNT(*) > 1
);
INSERT INTO skt_multiple_matches
SELECT parsed_id, master_id, parsed_lemma, master_lemma_trim, parsed_entry_str, master_entry_str, TRUE
FROM temp_skt_joined t
WHERE parsed_id NOT IN (
	SELECT DISTINCT parsed_id FROM skt_exact_matches
) AND master_id IN (
	SELECT DISTINCT master_id FROM skt_exact_matches
) AND parsed_id IN (
	SELECT parsed_id FROM temp_skt_joined
    GROUP BY parsed_id HAVING COUNT(*) > 1
);
SELECT * FROM skt_multiple_matches
ORDER BY CAST(REPLACE(parsed_id, '*', '') AS UNSIGNED), master_id;

-- Populate single unique matches
-- (master_id not paired to another - review only for approval - likely transcription issues)
TRUNCATE TABLE skt_single_matches;
INSERT INTO skt_single_matches
SELECT parsed_id, master_id, parsed_lemma, master_lemma_trim, parsed_entry_str, master_entry_str
FROM temp_skt_joined t
WHERE parsed_id NOT IN (
	SELECT DISTINCT parsed_id FROM skt_exact_matches
) AND master_id NOT IN (
	SELECT DISTINCT master_id FROM skt_exact_matches
) AND parsed_id IN (
	SELECT parsed_id FROM temp_skt_joined
    GROUP BY parsed_id HAVING COUNT(*) <= 1
);
SELECT * FROM skt_single_matches
ORDER BY CAST(REPLACE(parsed_id, '*', '') AS UNSIGNED), master_id;

-- Populate single repeat matches
-- (master_id already assigned to another lemma -- possibly new IDs?)
TRUNCATE TABLE skt_repeat_matches;
INSERT INTO skt_repeat_matches
SELECT parsed_id, master_id, parsed_lemma, master_lemma_trim, parsed_entry_str, master_entry_str
FROM temp_skt_joined t
WHERE parsed_id NOT IN (
	SELECT DISTINCT parsed_id FROM skt_exact_matches
) AND master_id IN (
	SELECT DISTINCT master_id FROM skt_exact_matches
) AND parsed_id IN (
	SELECT parsed_id FROM temp_skt_joined
    GROUP BY parsed_id HAVING COUNT(*) <= 1
);
SELECT * FROM skt_repeat_matches
ORDER BY CAST(REPLACE(parsed_id, '*', '') AS UNSIGNED), master_id;


-- Query all match groups
-- Exact matches (auto-approved)
SELECT * FROM skt_exact_matches
ORDER BY CAST(REPLACE(parsed_id, '*', '') AS UNSIGNED), master_id;
-- Single unique matches (need review, but likely approved)
SELECT * FROM skt_single_matches
ORDER BY CAST(REPLACE(parsed_id, '*', '') AS UNSIGNED), master_id;
-- Single repeat matches (likely new lemmas)
SELECT * FROM skt_repeat_matches
ORDER BY CAST(REPLACE(parsed_id, '*', '') AS UNSIGNED), master_id;
-- Multiple matches (manual review - may be new or match with now-split entry)
SELECT * FROM skt_multiple_matches
ORDER BY CAST(REPLACE(parsed_id, '*', '') AS UNSIGNED), master_id;
-- No matches (likely new lemmas)
SELECT * FROM skt_no_matches
ORDER BY CAST(REPLACE(parsed_id, '*', '') AS UNSIGNED);
-- Number of entries in each table
SELECT 
	(SELECT COUNT(*) FROM skt_exact_matches) AS exact,
    (SELECT COUNT(*) FROM skt_single_matches) AS single,
    (SELECT COUNT(*) FROM skt_repeat_matches) AS `repeat`,
    (SELECT COUNT(*) FROM skt_multiple_matches) AS multiple,
    (SELECT COUNT(*) FROM skt_no_matches) AS unmatched;
    
-- Resolving skt_single_matches: 
-- Check for transcription discrepancies (viz. does end of entry_str match?)
DROP TABLE IF EXISTS skt_approved_matches, skt_duplicate_matches;
CREATE TABLE skt_approved_matches AS
SELECT * FROM skt_exact_matches;
CREATE TABLE skt_duplicate_matches AS
SELECT * FROM skt_approved_matches 
WHERE master_id IN (
	SELECT master_id FROM skt_approved_matches
    GROUP BY master_id HAVING COUNT(*) > 1
);
SET SQL_SAFE_UPDATES = 0;
DELETE FROM skt_approved_matches
WHERE parsed_id IN (
	SELECT DISTINCT parsed_id FROM skt_duplicate_matches
);
-- Stats
SELECT 
	(SELECT COUNT(*) FROM temp_skt_parsed) AS total,
    (SELECT COUNT(*) FROM skt_approved_matches) AS approved,
    (SELECT COUNT(*) FROM skt_duplicate_matches) AS duplicates,
    ((SELECT COUNT(*) FROM temp_skt_parsed) - (SELECT COUNT(*) FROM skt_approved_matches) - (SELECT COUNT(DISTINCT(parsed_id)) FROM skt_duplicate_matches)) AS remaining;
    
    
-- Preprocess skt_single_matches for matching
DROP TABLE IF EXISTS temp_match_proc;
CREATE TABLE temp_match_proc AS
SELECT *, REGEXP_REPLACE(REGEXP_REPLACE(parsed_entry_str, '^.*?\\)[ ]*(?:[mfn]{1,3}\.)', ''), ' +', ' ') AS parsed_entry_normalized
FROM skt_single_matches;
SELECT * FROM temp_match_proc
ORDER BY CAST(REPLACE(parsed_id, '*', '') AS UNSIGNED);

-- Insert entries which differ only by transcription
-- Get substring from parsed_entry_str by extracting text after first literal ')'
DROP FUNCTION IF EXISTS match_after_p1;
DROP FUNCTION IF EXISTS match_after_p2;
DROP FUNCTION IF EXISTS match_after_p3;
DROP FUNCTION IF EXISTS match_after_p4;
DROP FUNCTION IF EXISTS match_pfx;
DELIMITER //
-- Return true if entry strings match after first closing parenthesis
CREATE FUNCTION match_after_p1 (parsed_entry_str MEDIUMTEXT, master_entry_str MEDIUMTEXT)
RETURNS BOOLEAN
DETERMINISTIC
NO SQL
BEGIN
	DECLARE parsed_substr MEDIUMTEXT;
    SET parsed_substr = REGEXP_REPLACE(parsed_entry_str, '^(.*?[\u0900-\u097F\u0980-\u09FF\uA8E0-\uA8FF]\\)){1,4}[ ]*(?:[mfn]{1,3}\.)', '');
    SET parsed_substr = REGEXP_REPLACE(parsed_substr, ' +', ' ');
    RETURN CHAR_LENGTH(parsed_substr) > 1 AND RIGHT(master_entry_str, CHAR_LENGTH(parsed_substr)) = parsed_substr;
END//
-- Return true if entry strings match after second closing parenthesis (i.e. two orthographies)
-- CREATE FUNCTION match_after_p2 (parsed_entry_str MEDIUMTEXT, master_entry_str MEDIUMTEXT)
-- RETURNS BOOLEAN
-- DETERMINISTIC
-- NO SQL
-- BEGIN
-- 	DECLARE parsed_substr MEDIUMTEXT;
--     SET parsed_substr = REGEXP_REPLACE(parsed_entry_str, '^.*?\\).*?\\)[ ]*(?:[mfn]{1,3}\.)', '');
--     SET parsed_substr = REGEXP_REPLACE(parsed_substr, ' +', ' ');
--     RETURN CHAR_LENGTH(parsed_substr) > 1 AND RIGHT(master_entry_str, CHAR_LENGTH(parsed_substr)) = parsed_substr;
-- END//
-- CREATE FUNCTION match_after_p3 (parsed_entry_str MEDIUMTEXT, master_entry_str MEDIUMTEXT)
-- RETURNS BOOLEAN
-- DETERMINISTIC
-- NO SQL
-- BEGIN
-- 	DECLARE parsed_substr MEDIUMTEXT;
--     SET parsed_substr = REGEXP_REPLACE(parsed_entry_str, '^.*?\\).*?\\).*?\\)[ ]*(?:[mfn]{1,3}\.)', '');
--     SET parsed_substr = REGEXP_REPLACE(parsed_substr, ' +', ' ');
--     RETURN CHAR_LENGTH(parsed_substr) > 1 AND RIGHT(master_entry_str, CHAR_LENGTH(parsed_substr)) = parsed_substr;
-- END//
-- CREATE FUNCTION match_after_p4 (parsed_entry_str MEDIUMTEXT, master_entry_str MEDIUMTEXT)
-- RETURNS BOOLEAN
-- DETERMINISTIC
-- NO SQL
-- BEGIN
-- 	DECLARE parsed_substr MEDIUMTEXT;
--     SET parsed_substr = REGEXP_REPLACE(parsed_entry_str, '^.*?\\).*?\\).*?\\).*?\\)[ ]*(?:[mfn]{1,3}\.)', '');
--     SET parsed_substr = REGEXP_REPLACE(parsed_substr, ' +', ' ');
--     RETURN CHAR_LENGTH(parsed_substr) > 1 AND RIGHT(master_entry_str, CHAR_LENGTH(parsed_substr)) = parsed_substr;
-- END//
CREATE FUNCTION match_pfx (parsed_entry_str MEDIUMTEXT, master_entry_str MEDIUMTEXT)
RETURNS BOOLEAN
DETERMINISTIC
NO SQL
BEGIN
	DECLARE parsed_normal MEDIUMTEXT;
    SET parsed_normal = REGEXP_REPLACE(parsed_entry_str, ' +', ' ');
    RETURN CHAR_LENGTH(parsed_normal) > 1 AND LEFT(master_entry_str, CHAR_LENGTH(parsed_normal)) = parsed_normal;
END//
DELIMITER ;

-- SELECT REGEXP_REPLACE('a-kāla—ja (अ-काल—ज) or a-kāla—jāta (अ-काल—जात) or akālôtpanna (अकालो̂त्पन्न),   mfn. born at a wrong time, unseasonable.', '^.*?\\).*?\\)[ ]*', '');

INSERT INTO skt_approved_matches
SELECT * FROM skt_single_matches
WHERE match_after_p1(parsed_entry_str, master_entry_str) = TRUE;
SET SQL_SAFE_UPDATES = 0;
DELETE FROM skt_single_matches
WHERE match_after_p1(parsed_entry_str, master_entry_str) = TRUE;
SET SQL_SAFE_UPDATES = 1;

-- INSERT INTO skt_approved_matches
-- SELECT * FROM skt_single_matches
-- WHERE match_after_p2(parsed_entry_str, master_entry_str) = TRUE;
-- SET SQL_SAFE_UPDATES = 0;
-- DELETE FROM skt_single_matches
-- WHERE match_after_p2(parsed_entry_str, master_entry_str) = TRUE;
-- SET SQL_SAFE_UPDATES = 1;

-- INSERT INTO skt_approved_matches
-- SELECT * FROM skt_single_matches
-- WHERE match_after_p3(parsed_entry_str, master_entry_str) = TRUE;
-- SET SQL_SAFE_UPDATES = 0;
-- DELETE FROM skt_single_matches
-- WHERE match_after_p3(parsed_entry_str, master_entry_str) = TRUE;
-- SET SQL_SAFE_UPDATES = 1;

-- INSERT INTO skt_approved_matches
-- SELECT * FROM skt_single_matches
-- WHERE match_after_p4(parsed_entry_str, master_entry_str) = TRUE;
-- SET SQL_SAFE_UPDATES = 0;
-- DELETE FROM skt_single_matches
-- WHERE match_after_p4(parsed_entry_str, master_entry_str) = TRUE;
-- SET SQL_SAFE_UPDATES = 1;

INSERT INTO skt_approved_matches
SELECT * FROM skt_single_matches
WHERE match_pfx(parsed_entry_str, master_entry_str) = TRUE;
SET SQL_SAFE_UPDATES = 0;
DELETE FROM skt_single_matches
WHERE match_pfx(parsed_entry_str, master_entry_str) = TRUE;
SET SQL_SAFE_UPDATES = 1;

-- Update single_matches with paired lemmas
-- INSERT INTO skt_repeat_matches
-- SELECT * FROM skt_single_matches
-- WHERE master_id IN (
-- 	SELECT DISTINCT master_id FROM skt_approved_matches
-- );
-- SET SQL_SAFE_UPDATES = 0;
-- DELETE FROM skt_single_matches
-- WHERE master_id IN (
-- 	SELECT DISTINCT master_id FROM skt_approved_matches
-- );
-- SET SQL_SAFE_UPDATES = 1;

-- Remove duplicates to duplicate table
INSERT INTO skt_duplicate_matches
SELECT * FROM skt_approved_matches
WHERE master_id IN (
	SELECT master_id FROM skt_approved_matches
	GROUP BY master_id HAVING COUNT(*) > 1
);
SET SQL_SAFE_UPDATES = 0;
DELETE FROM skt_approved_matches
WHERE parsed_id IN (
	SELECT DISTINCT parsed_id FROM skt_duplicate_matches
);
SET SQL_SAFE_UPDATES = 1;

SELECT * FROM skt_approved_matches
WHERE master_id IN (
	SELECT master_id FROM skt_approved_matches
	GROUP BY master_id HAVING COUNT(*) > 1
);
SELECT * FROM skt_duplicate_matches;