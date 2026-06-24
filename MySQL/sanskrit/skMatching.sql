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
ALTER TABLE skt_exact_matches ADD PRIMARY KEY (parsed_id, master_id);
CREATE TABLE skt_repeat_matches LIKE skt_exact_matches;
CREATE TABLE skt_single_matches LIKE skt_exact_matches;
CREATE TABLE skt_multiple_matches LIKE skt_exact_matches;
ALTER TABLE skt_multiple_matches ADD COLUMN master_lemma_paired BOOLEAN;
-- Query entries with no match
CREATE TABLE skt_no_matches AS 
SELECT parsed_id, parsed_lemma, parsed_entry_str 
FROM temp_skt_joined WHERE master_id IS NULL;
-- Table to store results of query of single lemma
-- CREATE TABLE skt_lemma_match LIKE skt_exact_matches;
-- DESCRIBE skt_lemma_match;

DELIMITER //
-- Function returns True if provided row in skt_lemma_match can be auto-approved as an exact match
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
TRUNCATE skt_exact_matches;
INSERT INTO skt_exact_matches
SELECT parsed_id, master_id, parsed_lemma, master_lemma_trim, parsed_entry_str, master_entry_str
FROM temp_skt_joined
WHERE exact_match(parsed_entry_str, master_entry_str) = TRUE;
SELECT * FROM skt_exact_matches ORDER BY CAST(REPLACE(parsed_id, '*', '') AS UNSIGNED), master_id;

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
SELECT *, exact_match(parsed_entry_str, master_entry_str) AS exact FROM skt_multiple_matches
ORDER BY CAST(REPLACE(parsed_id, '*', '') AS UNSIGNED), master_id;