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
-- (lemma_id,lang,lemma,sense_num,`type`,orthography,ipa,pos,gender,etymology,entry,entry_str,gloss,sense_id,h_number,parent_h_number);
(lemma_id,lang,lemma,sense_num,`type`,orthography,ipa,pos,gender,etymology,entry,entry_str,gloss,sense_id,h_number,parent_h_number,lemma_normalized,lemma_translit);

-- Fill in lang field, if needed
SET SQL_SAFE_UPDATES=0;
UPDATE temp_parsed
SET lang = @lang_code
WHERE lang IS NULL;
SET SQL_SAFE_UPDATES=1;
SELECT * FROM temp_parsed;

-- Merge temporary tables with lex_master & lex_senses
START TRANSACTION;
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
FROM temp_parsed
WHERE `type` != "sense";

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
FROM temp_parsed
WHERE `type` = "sense";

-- ROLLBACK;
COMMIT;