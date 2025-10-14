USE derbi_pie_sql;
CREATE TABLE `lex_ref_link` (
  `orig_lang_abbrev` varchar(255) DEFAULT NULL,
  `lang` varchar(20) DEFAULT NULL,
  `lex_ref_link_id` varchar(255) NOT NULL,
  `ref_id` varchar(255) DEFAULT NULL,
  `rt_ref_link_id` varchar(255) DEFAULT NULL,
  `ref_rt_index` varchar(255) DEFAULT NULL,
  `word_id` varchar(255) DEFAULT NULL,
  `ref_wd_index` varchar(255) DEFAULT NULL,
  `reflex` varchar(255) DEFAULT NULL,
  `category` varchar(255) DEFAULT NULL,
  `gloss_orig` text,
  `gloss_eng` text,
  `page_loc` varchar(20) DEFAULT NULL,
  `questionable` tinyint(1) DEFAULT NULL,
  `notes` text,
  `expanded_notes` text,
  `original_text` text,
  `created_by` varchar(255) DEFAULT NULL,
  `last_updated` datetime DEFAULT NULL,
  `last_updated_by` varchar(255) DEFAULT NULL,
  `derivation` varchar(255) DEFAULT NULL,
  `rt_ref_link_id_old` varchar(255) DEFAULT NULL,
  `rt_ref_link_id_1` varchar(255) DEFAULT NULL,
  `rt_index` varchar(255) DEFAULT NULL,
  `rt_master_id` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`lex_ref_link_id`),
  KEY `lex_ref_link_ref_id_index` (`ref_id`),
  KEY `lex_ref_link_rt_ref_link_id_index` (`rt_ref_link_id`),
  KEY `lex_ref_link_word_id_index` (`word_id`),
  KEY `lex_ref_link_rt_index_foreign` (`ref_rt_index`)
  -- CONSTRAINT `lex_ref_link_rt_ref_link_id_foreign` FOREIGN KEY (`rt_ref_link_id`) REFERENCES `rt_ref_link` (`rt_ref_link_id`),
--   CONSTRAINT `lex_ref_link_word_id_foreign` FOREIGN KEY (`word_id`) REFERENCES `lex_master` (`word_id`)
) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
ALTER TABLE lex_ref_link CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE lex_ref_link MODIFY COLUMN questionable INT DEFAULT NULL;
ALTER TABLE lex_ref_link MODIFY COLUMN lex_ref_link_id INT;
SHOW VARIABLES LIKE 'character_set%';
SELECT table_schema, table_name, column_name, character_set_name, collation_name FROM information_schema.COLUMNS WHERE table_name = 'lex_ref_link';
SET NAMES utf8mb4;
DROP TABLE lex_ref_link;

# Load data from CSV
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/lex_ref_link_conv.csv'
INTO TABLE lex_ref_link
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(rt_ref_link_id,rt_ref_link_id_old,orig_lang_abbrev,lex_ref_link_id,ref_id,ref_rt_index,word_id,ref_wd_index,reflex,category,gloss_orig,gloss_eng,@questionable,notes,expanded_notes,original_text,created_by,last_updated_by,last_updated,rt_master_id,derivation,rt_index)
SET questionable = NULLIF(@questionable, '');

SELECT * FROM lex_ref_link WHERE orig_lang_abbrev = 'lat.' ORDER BY lex_ref_link_id;

# Fix '#NAME' entries
SELECT * FROM lex_ref_link WHERE reflex LIKE '#NAME%' AND orig_lang_abbrev LIKE '%lat%';

TRUNCATE TABLE lex_ref_link;