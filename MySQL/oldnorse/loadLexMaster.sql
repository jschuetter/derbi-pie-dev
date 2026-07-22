USE derbi_pie_jacob;
-- Staging table to load data from CSV, to be split into lex_master and lex_senses
DROP TABLE IF EXISTS master_stg;
-- Master table, including all columns in lex_master AND lex_senses
CREATE TABLE master_stg (
    `lemma_id` int NOT NULL,
    `lemma` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
    `sense_num` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
    `page_num` int DEFAULT NULL,
    `type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
    `orthography` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
    `ipa` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
    `pos` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
    `gender` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
    `stem` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
    `etymology` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
    `entry` mediumtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
    `entry_str` mediumtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
    `last_updated` datetime DEFAULT NULL,
    `editor` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
    `components` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
    `gloss` text COLLATE utf8mb4_unicode_ci,
    `sense_id` int DEFAULT NULL,
    `h_number` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
    `parent_h_number` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL
);

# Load data from CSV
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/zoega.csv'
INTO TABLE master_stg
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(lemma_id,lemma,sense_num,`type`,ipa,pos,gender,entry,entry_str,gloss,sense_id,h_number,parent_h_number);
-- Above line matches column ordering in CSV (using names in master_stg)

-- Insert data from master_stg into lex_master
START TRANSACTION;
INSERT INTO lex_master 
(
	`lemma_id`,
    `lang`,
    `lemma`,
    `lemma_normalized`,
    `lemma_translit`,
    `sense_num`,
    `page_num`,
    `type`,
    `orthography`,
    `ipa`,
    `pos`,
    `gender`,
    `stem`,
    `etymology`,
    `etymology_resolved`,
    `entry`,
    `entry_str`,
    `last_updated`,
    `editor`,
    `components`,
    `gloss`,
    `entry_type`
) 
SELECT 
    lemma_id, 
	'ON', 
    lemma, 
    lemma, 
    lemma, 
    sense_num, 
    NULL, 
    `type`, 
    NULL, 
    ipa,
    pos, 
    gender,
    NULL,
    NULL,
    NULL,
    `entry`,
    entry_str,
    CURTIME(),
    'JMS',
    NULL,
    gloss,
    NULL
FROM master_stg
WHERE `type` != 'sense';

-- Copy sense data from master_stg
INSERT INTO lex_senses 
(
	`sense_id`,
    `lang`,
    `lemma_id`,
    `lemma`,
    `sense_num`,
    `page_num`,
    `entry`,
    `entry_str`,
    `last_updated`,
    `editor`,
    `h_number`,
    `parent_h_number`,
    `gloss`
)
SELECT 
    sense_id, 
	'ON', 
    lemma_id, 
    lemma,
    sense_num, 
    NULL,
    `entry`,
    entry_str,
    CURTIME(),
    'JMS',
    h_number,
    parent_h_number,
    gloss
FROM master_stg
WHERE `type` = 'sense';

COMMIT;

DROP TABLE master_stg;
SELECT * FROM lex_master WHERE lang = 'ON';
SELECT * FROM lex_senses WHERE lang = 'ON';