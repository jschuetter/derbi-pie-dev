DROP TABLE IF EXISTS temp_oe_parsed;
CREATE TABLE temp_oe_parsed LIKE lex_master;
ALTER TABLE temp_oe_parsed
DROP PRIMARY KEY,
ADD COLUMN sense_id INT,
ADD COLUMN h_number VARCHAR(20),
ADD COLUMN parent_h_number VARCHAR(20);

-- Load data from CSV
TRUNCATE TABLE temp_oe_parsed;
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/bosworth-toller-renumbered.csv'
INTO TABLE temp_oe_parsed
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(lemma_id,lemma,sense_num,page_num,`type`,ipa,orthography,pos,gender,etymology,entry,entry_str,gloss,sense_id,h_number,parent_h_number);
-- (lemma_id,lemma,lemma_normalized,lemma_translit,sense_num,page_num,`type`,ipa,orthography,pos,gender,etymology,entry,entry_str,gloss,entry_type,@sense_id,h_number,parent_h_number);

-- Fill in lang field
SET SQL_SAFE_UPDATES=0;
UPDATE temp_oe_parsed
SET lang = 'OE';
SET SQL_SAFE_UPDATES=1;
SELECT * FROM temp_oe_parsed;

-- Split into master & senses

-- Merge temporary tables with lex_master & lex_senses
START TRANSACTION;
-- DESCRIBE lex_master;
DELETE FROM lex_senses
WHERE lang = 'OE';
DELETE FROM lex_master 
WHERE lang = 'OE';
INSERT INTO lex_master
SELECT 
	lemma_id,
    lang,
    lemma,
    lemma_normalized,
    lemma_translit,
    sense_num,
    page_num,
    `type`,
    orthography,
    ipa,
    pos,
    gender,
    stem,
    etymology,
    etymology_resolved,
    entry,
    entry_str,
    NOW(),
    'JMS',
    components,
    gloss,
    entry_type,
    related
FROM temp_oe_parsed
WHERE `type` != "sense";
-- 36160 inserted
-- DESCRIBE lex_senses;
INSERT INTO lex_senses
SELECT 
	sense_id,
    lang,
    lemma_id,
    lemma,
    sense_num,
    page_num,
    entry,
    entry_str,
    NOW(),
    'JMS',
    h_number,
    parent_h_number,
    gloss
FROM temp_oe_parsed
WHERE `type` = "sense";
-- 4089 inserted
-- ROLLBACK;
COMMIT;