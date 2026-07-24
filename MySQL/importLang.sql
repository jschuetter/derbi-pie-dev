SET @lang_code = 'OCS';

DROP TABLE IF EXISTS temp_parsed;
CREATE TABLE temp_parsed LIKE lex_master;
ALTER TABLE temp_parsed
DROP PRIMARY KEY,
ADD COLUMN sense_id INT,
ADD COLUMN h_number VARCHAR(20),
ADD COLUMN parent_h_number VARCHAR(20);

-- Load data from CSV
TRUNCATE TABLE temp_parsed;
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/old-church-slavonic.csv'
INTO TABLE temp_parsed
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(lemma_id,lemma,sense_num,`type`,orthography,ipa,pos,gender,etymology,entry,entry_str,gloss,lemma_normalized,lemma_translit);
-- (lemma_id,lemma,sense_num,page_num,`type`,ipa,orthography,pos,gender,etymology,entry,entry_str,gloss,sense_id,h_number,parent_h_number);
-- (lemma_id,lemma,lemma_normalized,lemma_translit,sense_num,page_num,`type`,ipa,orthography,pos,gender,etymology,entry,entry_str,gloss,entry_type,@sense_id,h_number,parent_h_number);

-- Fill in lang field
SET SQL_SAFE_UPDATES=0;
UPDATE temp_parsed
SET lang = @lang_code;
SET SQL_SAFE_UPDATES=1;
SELECT * FROM temp_parsed;

-- Split into master & sense tables
-- (allows auto-incrementing sense_id if necessary)
DROP TABLE IF EXISTS temp_master, temp_senses;
CREATE TABLE temp_master LIKE lex_master;
CREATE TABLE temp_senses LIKE lex_senses;
ALTER TABLE temp_senses DROP PRIMARY KEY;
ALTER TABLE temp_senses MODIFY COLUMN sense_id INT PRIMARY KEY AUTO_INCREMENT;

INSERT INTO temp_master
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
FROM temp_parsed
WHERE `type` != "sense";

INSERT INTO temp_senses
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
FROM temp_parsed
WHERE `type` = "sense";

SELECT * FROM temp_master;
SELECT * FROM temp_senses;

-- Merge temporary tables with lex_master & lex_senses
START TRANSACTION;
INSERT INTO lex_master
SELECT * FROM temp_master;
INSERT INTO lex_senses
SELECT * FROM temp_senses;
-- ROLLBACK;
-- COMMIT;