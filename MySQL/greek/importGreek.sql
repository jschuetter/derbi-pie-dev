DROP TABLE IF EXISTS temp_gk_parsed;
CREATE TABLE temp_gk_parsed LIKE lex_master;
ALTER TABLE temp_gk_parsed
DROP PRIMARY KEY,
ADD COLUMN sense_id INT,
ADD COLUMN h_number VARCHAR(20),
ADD COLUMN parent_h_number VARCHAR(20);

DROP TABLE IF EXISTS gk_master, gk_senses;
CREATE TABLE gk_master LIKE lex_master;
CREATE TABLE gk_senses LIKE lex_senses;

-- Load data from CSV (needs to be repeated!)
TRUNCATE TABLE temp_gk_parsed;
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/matching/greek/grc.lsj.perseus-eng1.csv'
INTO TABLE temp_gk_parsed
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(lemma_id,lemma,lemma_normalized,lemma_translit,sense_num,page_num,`type`,ipa,orthography,pos,gender,etymology,entry,entry_str,gloss,entry_type,sense_id,h_number,parent_h_number);

-- Check join with lex_master
SELECT gk.lemma_id, gk.type, gk.lemma, lm.lemma, gk.entry_str, lm.entry_str
FROM temp_gk_parsed gk
LEFT JOIN lex_master lm
ON gk.lemma_id = lm.lemma_id
AND lm.lang = 'Gk.'
WHERE gk.`type` != 'sense';