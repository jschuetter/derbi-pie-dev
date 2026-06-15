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
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/skt-id-resolutions.csv'
INTO TABLE master_stg
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(lemma_id,lemma,sense_id,entry, entry_str);
-- Above line matches column ordering in CSV (using names in master_stg)

SELECT * FROM master_stg;

START TRANSACTION;

UPDATE lex_senses
INNER JOIN master_stg
ON lex_senses.lang = 'Skt.'
AND lex_senses.lemma_id = master_stg.lemma_id
AND lex_senses.sense_id = master_stg.sense_id
SET lex_senses.entry = master_stg.entry_str,
lex_senses.entry_str = master_stg.entry_str;

SELECT * FROM lex_senses
WHERE EXISTS (
	SELECT sense_id FROM master_stg WHERE master_stg.sense_id = lex_senses.sense_id
) AND lex_senses.lang = "Skt.";

COMMIT;