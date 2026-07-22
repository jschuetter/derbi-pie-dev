-- Load parsed data
DROP TABLE IF EXISTS temp_skt_parsed;
CREATE TABLE temp_skt_parsed LIKE lex_master;
ALTER TABLE temp_skt_parsed MODIFY COLUMN lemma_id VARCHAR(16);
ALTER TABLE temp_skt_parsed MODIFY COLUMN gender VARCHAR(29);
ALTER TABLE temp_skt_parsed DROP PRIMARY KEY;
ALTER TABLE temp_skt_parsed 
ADD COLUMN related VARCHAR(16),
ADD COLUMN sense_id VARCHAR(16),
ADD COLUMN h_number VARCHAR(20),
ADD COLUMN parent_h_number VARCHAR(20);
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/monier-williams-tempidx.csv'
INTO TABLE temp_skt_parsed
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(lemma_id,lemma,lemma_normalized,lemma_translit,sense_num,page_num,`type`,orthography,pos,gender,etymology,entry,entry_str,components,gloss,related,sense_id,h_number,parent_h_number);

-- [A] - Reindex approved matches
-- Import approved match pairings to new temporary table
DROP TABLE IF EXISTS skt_approved_matches;
CREATE TABLE skt_approved_matches(
	parsed_id VARCHAR(64) UNIQUE,
    master_id INT UNIQUE,
    PRIMARY KEY (parsed_id, master_id)
);
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/skt_approved_matches_v2.csv'
INTO TABLE skt_approved_matches
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(parsed_id, master_id);

-- Create new temporary table for reindexed matches
DROP TABLE IF EXISTS temp_skt_reindexed_main, temp_skt_reindexed_senses;
CREATE TABLE temp_skt_reindexed_main LIKE lex_master;
ALTER TABLE temp_skt_reindexed_main 
MODIFY COLUMN gender VARCHAR(29),
MODIFY COLUMN lemma_id INT,
ADD COLUMN related INT;
CREATE TABLE temp_skt_reindexed_senses LIKE lex_senses;

-- (1) - Generate indices for new entries
-- Add to skt_approved_matches for substitution below
SELECT id, ROW_NUMBER() OVER (ORDER BY CAST(REPLACE(id, '*', '') AS UNSIGNED))
FROM (
	SELECT DISTINCT lemma_id AS id
    FROM temp_skt_parsed
	LEFT JOIN skt_approved_matches
	ON lemma_id COLLATE utf8mb4_unicode_ci = parsed_id
	WHERE parsed_id IS NULL
) d LIMIT 1000;
SELECT MAX(lemma_id) FROM lex_master WHERE lang = 'Skt.' INTO @max_id;
-- Export to file
-- SELECT id AS parsed_id, ROW_NUMBER() OVER (ORDER BY CAST(REPLACE(id, '*', '') AS UNSIGNED)) + @max_id AS master_id
-- FROM (
-- 	SELECT DISTINCT lemma_id AS id
--     FROM temp_skt_parsed
-- 	LEFT JOIN skt_approved_matches
-- 	ON lemma_id COLLATE utf8mb4_unicode_ci = parsed_id
-- 	WHERE parsed_id IS NULL
-- ) d 
-- INTO OUTFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/exports/skt_new_indices.csv'
-- CHARACTER SET utf8mb4
-- FIELDS TERMINATED BY ',' 
-- ESCAPED BY '\\'
-- ENCLOSED BY '"'
-- LINES TERMINATED BY '\r\n' ;
-- Insert to skt_approved_matches
INSERT INTO skt_approved_matches
SELECT id AS parsed_id, ROW_NUMBER() OVER (ORDER BY CAST(REPLACE(id, '*', '') AS UNSIGNED)) + @max_id AS master_id
FROM (
	SELECT DISTINCT lemma_id AS id
    FROM temp_skt_parsed
	LEFT JOIN skt_approved_matches
	ON lemma_id COLLATE utf8mb4_unicode_ci = parsed_id
	WHERE parsed_id IS NULL
) d;

-- (2) - Update each row in `temp_skt_parsed` using regexp
DROP FUNCTION IF EXISTS sub_id;
DELIMITER //
CREATE FUNCTION sub_id (temp_id VARCHAR(64))
RETURNS VARCHAR(64)
READS SQL DATA
BEGIN
	DECLARE re VARCHAR(64);
    DECLARE id_group VARCHAR(64);
    DECLARE id_sub VARCHAR(64);
    DECLARE err_msg VARCHAR(64);
    
    IF temp_id IS NULL THEN
		RETURN NULL;
	END IF;
    
    SET re = '\\*[0-9]{1,7}';
    SET id_group = REGEXP_SUBSTR(temp_id, re);
    IF id_group IS NULL THEN
		SET err_msg = CONCAT('ID group not found in parsed_id ', temp_id);
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = err_msg;
	END IF;
    
    SET id_sub = (SELECT master_id FROM skt_approved_matches WHERE parsed_id = id_group);
    IF id_sub IS NULL THEN
		SET err_msg = CONCAT('Match not found for parsed_id ', id_group);
		SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = err_msg;
	END IF;
	RETURN REGEXP_REPLACE(temp_id, re, id_sub);
END//
DELIMITER ;

-- Insert matched rows to reindexed tables
TRUNCATE TABLE temp_skt_reindexed_main;
TRUNCATE TABLE temp_skt_reindexed_senses;
SELECT COUNT(*) FROM temp_skt_parsed WHERE `type` = 'main';
SELECT MAX(master_id) FROM skt_approved_matches;

INSERT INTO temp_skt_reindexed_main
SELECT CAST(sub_id(lemma_id) AS UNSIGNED), 
	'Skt.', lemma, lemma_normalized,
	lemma_translit, sense_num, page_num, `type`, orthography,
	ipa, pos, gender, stem, etymology, etymology_resolved,
	entry, entry_str, last_updated, editor, components, gloss, entry_type,
	CAST(sub_id(related) AS UNSIGNED)
FROM temp_skt_parsed
WHERE `type` = 'main'
LIMIT 100000
OFFSET 200000; -- Repeat in intervals of 100000 (3 slices)

INSERT INTO temp_skt_reindexed_senses
SELECT CAST(REPLACE(sense_id, '*', '') AS UNSIGNED),
	'Skt.',
    CAST(sub_id(lemma_id) AS UNSIGNED), 
	lemma, sense_num, page_num, 
    entry, entry_str, last_updated, 
    editor,
	sub_id(h_number),
	sub_id(parent_h_number),
    gloss
FROM temp_skt_parsed
WHERE `type` = 'sense';

SELECT rm.lemma_id, rm.lemma_translit, lm.lemma AS master_lemma, rm.entry_str, lm.entry_str AS master_entry
FROM temp_skt_reindexed_main rm
JOIN lex_master lm
ON rm.lemma_id = lm.lemma_id
AND rm.lang = lm.lang;

SELECT s.sense_id, s.lemma_id, s.lemma, m.lemma AS main_lemma, s.entry_str, m.entry_str AS main_entry
FROM temp_skt_reindexed_senses s
LEFT JOIN temp_skt_reindexed_main m
ON s.lemma_id = m.lemma_id;

-- Export new things to file
SELECT * FROM temp_skt_reindexed_main
ORDER BY lemma_id
INTO OUTFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/exports/skt_reindexed_main.csv'
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' 
ESCAPED BY '"'
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n' ;

SELECT * FROM temp_skt_reindexed_senses
ORDER BY lemma_id
INTO OUTFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/exports/skt_reindexed_senses.csv'
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' 
ESCAPED BY '"'
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n' ;