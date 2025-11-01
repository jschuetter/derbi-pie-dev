DROP TABLE rt_master;
CREATE TABLE rt_master (
	rt_master_id INT PRIMARY KEY NOT NULL,
    rt_relationship VARCHAR(16),
    rt_shape VARCHAR(128) NOT NULL,
    rt_meaning VARCHAR(64),
    grammar VARCHAR(128)
);
ALTER TABLE rt_master MODIFY COLUMN grammar VARCHAR(128);

-- Import from CSV
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/rt_master(Sheet1).csv'
INTO TABLE rt_master
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(rt_master_id,rt_relationship,rt_shape,rt_meaning,grammar);

SELECT * FROM rt_master;

DROP TABLE lex_master;
CREATE TABLE lex_master (
	lang VARCHAR(64) NOT NULL,
    word_id INT PRIMARY KEY NOT NULL,
    reflex VARCHAR(64) NOT NULL,
    gloss VARCHAR(64),
    pos VARCHAR(64) NOT NULL,
    gender VARCHAR(64),
    `number` VARCHAR(64),
    stem VARCHAR(64),
    conceptsets MEDIUMTEXT,
    other_gramm_info TEXT,
    last_updated DATETIME,
    last_updated_by VARCHAR(64)
);

ALTER TABLE lex_master MODIFY COLUMN stem VARCHAR(64);
TRUNCATE TABLE lex_master;

-- Copy entries from Lewis & Short
-- Combine all senses into one entry - use plaintext in 'conceptsets' field?
-- Need to split pos field into pos + (gender - when noun)
-- Separate query for nouns
INSERT INTO lex_master (lang, word_id, reflex, pos, conceptsets, last_updated, last_updated_by)
SELECT 'latin' as lang, lemma_id, lemma, SUBSTRING(pos, 1, LOCATE('.', pos)) , entry_str, CURRENT_DATE(), 'jms'
FROM lewis_short
WHERE `type` != 'sense' AND SUBSTRING(pos, 1, 1) != 'n';

INSERT INTO lex_master (lang, word_id, reflex, pos, gender, conceptsets, last_updated, last_updated_by)
SELECT 'latin' as lang, lemma_id, lemma, SUBSTRING(pos, 1, LOCATE('.', pos)), SUBSTRING(pos, 4) AS gender, entry_str, CURRENT_DATE(), 'jms'
FROM lewis_short
WHERE `type` != 'sense' AND SUBSTRING(pos, 1, 1) = 'n';

SELECT * FROM lex_master;

DROP TABLE rt_ref_link;
CREATE TABLE rt_ref_link (
	rt_ref_link_id INT PRIMARY KEY NOT NULL,
    ref_id VARCHAR(8) NOT NULL,
    rt_master_id INT NOT NULL,
    ref_rt_index INT NOT NULL,
    rt_shape VARCHAR(256) NOT NULL,
    rt_gloss_orig VARCHAR(512),
    rt_gloss_eng VARCHAR(512),
    questionable_root VARCHAR(8),
    questionable_meaning VARCHAR(8),
    root_fn VARCHAR(8),
    gloss_fn VARCHAR(8),
    last_updated DATETIME,
    last_updated_by VARCHAR(8),
    rt_relationship VARCHAR(64),
    rt_relationship_rt_master VARCHAR(64)
);
ALTER TABLE rt_ref_link CHANGE rt_index ref_rt_index INT NOT NULL;

-- Import from CSV
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/rt_ref_link(Sheet1).csv'
INTO TABLE rt_ref_link
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(rt_ref_link_id,rt_master_id,ref_id,ref_rt_index,rt_shape,rt_gloss_orig,rt_gloss_eng,questionable_root,questionable_meaning,root_fn,gloss_fn,@last_updated,last_updated_by,rt_relationship,rt_relationship_rt_master)
SET 
last_updated = STR_TO_DATE(NULLIF(@last_updated, ''), '%Y_%m_%d_%h%i');

SELECT * FROM rt_ref_link;

DROP TABLE lang_abbrev_master;
CREATE TABLE lang_abbrev_master (
	abbrev_id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
    eng_abbrev VARCHAR(64) NOT NULL,
    source_abbrev VARCHAR(128) NOT NULL,
    full_language_name VARCHAR(64) NOT NULL,
    wikt_lang_key VARCHAR(64),
    lang_index VARCHAR(64) NOT NULL,
    Glottolog_lang VARCHAR(128) NOT NULL
);
ALTER TABLE lang_abbrev_master MODIFY COLUMN source_abbrev VARCHAR(128) NOT NULL;

TRUNCATE TABLE lang_abbrev_master;
-- Import from CSV
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/lang_abbrev_master(Sheet1).csv'
INTO TABLE lang_abbrev_master
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(eng_abbrev,source_abbrev,full_language_name,wikt_lang_key,lang_index,Glottolog_lang);

SELECT * FROM lang_abbrev_master;