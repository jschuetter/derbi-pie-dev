DROP TABLE IF EXISTS skt_exact_matches, skt_repeat_matches, skt_single_matches, skt_multiple_matches, skt_no_matches, skt_lemma_match, skt_duplicate_matches;
-- DROP TABLE IF EXISTS skt_approved_matches;
CREATE TABLE skt_approved_matches (
	parsed_id VARCHAR(64) UNIQUE,
    master_id VARCHAR(64) UNIQUE,
    parsed_lemma VARCHAR(64),
    master_lemma_trim VARCHAR(64),
    parsed_entry_str MEDIUMTEXT,
    master_entry_str MEDIUMTEXT,
    master_entry_resolved MEDIUMTEXT,
    PRIMARY KEY (parsed_id, master_id)
);
-- Temp table for loading matches (don't throw an error on duplicate PK)
CREATE TABLE skt_temp_matches LIKE skt_approved_matches;
ALTER TABLE skt_temp_matches DROP PRIMARY KEY;
CREATE TABLE skt_duplicate_matches LIKE skt_temp_matches;

-- Load data (repeat for each .csv of *approved matches* - don't forget to update columns!)
TRUNCATE TABLE skt_temp_matches;
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/matching/sanskrit/missing-parsed-approved.csv'
INTO TABLE skt_temp_matches
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(@levenshtein, parsed_id,master_id,parsed_lemma,master_lemma_trim,parsed_entry_str,master_entry_resolved,master_entry_str, @paired);
SELECT * FROM skt_temp_matches;

-- Check for duplicates
SELECT master_id, COUNT(*), GROUP_CONCAT(DISTINCT parsed_id SEPARATOR ", ") FROM skt_temp_matches 
GROUP BY master_id HAVING COUNT(*) > 1;

SELECT t.parsed_id, t.master_id, t.parsed_entry_str, a.parsed_id, a.master_id, a.parsed_entry_str, a.master_entry_str
FROM skt_temp_matches t
INNER JOIN skt_approved_matches a
ON t.master_id = a.master_id;
SELECT t.parsed_id, t.master_id, t.parsed_entry_str, t.master_entry_str, a.parsed_id, a.master_id, a.parsed_entry_str, a.master_entry_str
FROM skt_temp_matches t
INNER JOIN skt_approved_matches a
ON t.parsed_id = a.parsed_id;

SELECT * FROM skt_temp_matches WHERE parsed_id = "*100251";
SELECT entry_str FROM lex_master
WHERE lemma_id IN (171513,171511,119573,119527,143453,143440);

SELECT parsed_id, COUNT(*) FROM skt_temp_matches 
GROUP BY parsed_id HAVING COUNT(*) > 1;
-- Delete duplicates if needed
SET SQL_SAFE_UPDATES = 0;
DELETE FROM skt_temp_matches WHERE master_id = "143453" AND parsed_id = "*167946";
SET SQL_SAFE_UPDATES = 1;

-- If no duplicates, copy into skt_approved_matches
INSERT INTO skt_approved_matches
SELECT * FROM skt_temp_matches;
-- Alternative: insert into skt_approved_matches, filtering internal duplicates
-- and skipping already-assigned lemmas
INSERT INTO skt_approved_matches
SELECT DISTINCT * FROM skt_temp_matches;

-- Repeat match remediation
SELECT * FROM skt_approved_matches
WHERE master_id IN ('115513', '104698');
SELECT * FROM temp_skt_parsed
WHERE lemma_id IN ('*122569', '*122570');
SELECT * FROM lex_master lm
JOIN lex_senses ls
ON lm.lemma_id = ls.lemma_id
WHERE lm.lang = 'Skt.'
AND ls.lang = 'Skt.'
AND lm.lemma_id = 157523;

SELECT * FROM skt_approved_matches ORDER BY CAST(REPLACE(parsed_id, '*', '') AS UNSIGNED), master_id;


-- Check for missing pairings (1146 total: 462 have joins, 684 without)
-- After matching round 2: 818 total, 134 have joins (but aren't matches)
SELECT COUNT(*)
FROM lex_master lm
WHERE lang = 'Skt.'
AND lemma_id NOT IN (
	SELECT DISTINCT master_id
    FROM skt_approved_matches
);
SELECT COUNT(DISTINCT ts.master_id)
FROM lex_master lm
LEFT JOIN temp_skt_joined ts 
ON lm.lemma_id = ts.master_id
WHERE lang = 'Skt.'
AND lemma_id NOT IN (
	SELECT DISTINCT master_id
    FROM skt_approved_matches
);
SELECT COUNT(DISTINCT sp.lemma_id)
FROM temp_skt_parsed sp
LEFT JOIN temp_skt_joined sj
ON sp.lemma_id = sj.parsed_id COLLATE utf8mb4_unicode_ci 
WHERE lemma_id NOT IN (
	SELECT DISTINCT parsed_id COLLATE utf8mb4_unicode_ci 
    FROM skt_approved_matches
) 
AND sj.master_id IS NOT NULL
ORDER BY CAST(REPLACE(lemma_id, '*', '') AS UNSIGNED);

-- Export all potential matches for missing pairings
SELECT ts.*
FROM lex_master lm
JOIN temp_skt_joined ts 
ON lm.lemma_id = ts.master_id
WHERE lang = 'Skt.'
AND lemma_id NOT IN (
	SELECT DISTINCT master_id
    FROM skt_approved_matches
)
INTO OUTFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/exports/skt_missing_pairings.csv'
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' 
ESCAPED BY '\\'
ENCLOSED BY '"'
LINES TERMINATED BY '\n' ;
-- Export missing entries with no pairings
SELECT lm.*
FROM lex_master lm
LEFT JOIN temp_skt_joined ts 
ON lm.lemma_id = ts.master_id
WHERE lang = 'Skt.'
AND ts.parsed_id IS NULL
INTO OUTFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/exports/skt_missing_unmatched.csv'
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' 
ESCAPED BY '\\'
ENCLOSED BY '"'
LINES TERMINATED BY '\n' ;
SELECT * FROM lex_senses;
-- Do the same thing, but for missing parsed_id pairings!
SELECT tj.*
FROM temp_skt_parsed tp
JOIN temp_skt_joined tj
ON tp.lemma_id COLLATE utf8mb4_unicode_ci = tj.parsed_id
WHERE lemma_id COLLATE utf8mb4_unicode_ci NOT IN (
	SELECT DISTINCT parsed_id
    FROM skt_approved_matches
)
INTO OUTFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/exports/skt_parsed_missing_pairings.csv'
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' 
ESCAPED BY '\\'
ENCLOSED BY '"'
LINES TERMINATED BY '\n' ;
-- (No pairings)
SELECT tj.*
FROM temp_skt_parsed tp
JOIN temp_skt_joined tj
ON tp.lemma_id = tj.parsed_id COLLATE utf8mb4_unicode_ci
WHERE tj.master_id IS NULL
INTO OUTFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/exports/skt_parsed_missing_unmatched.csv'
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' 
ESCAPED BY '\\'
ENCLOSED BY '"'
LINES TERMINATED BY '\n' ;

-- Export approved matches
SELECT parsed_id, master_id
FROM skt_approved_matches
ORDER BY CAST(REPLACE(parsed_id, '*', '') AS UNSIGNED)
INTO OUTFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/exports/skt_approved_matches_v3.csv'
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' 
ESCAPED BY '\\'
ENCLOSED BY '"'
LINES TERMINATED BY '\n' ;