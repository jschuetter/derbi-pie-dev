-- Load parsed data
DROP TABLE IF EXISTS temp_skt_parsed;
CREATE TABLE temp_skt_parsed LIKE lex_master;
ALTER TABLE temp_skt_parsed MODIFY COLUMN lemma_id VARCHAR(16);
ALTER TABLE temp_skt_parsed MODIFY COLUMN gender VARCHAR(29);
ALTER TABLE temp_skt_parsed DROP PRIMARY KEY;
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/monier-williams-tempidx.csv'
INTO TABLE temp_skt_parsed
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(lemma_id,lemma,lemma_normalized,lemma_translit,sense_num,page_num,`type`,orthography,pos,gender,etymology,entry,entry_str,components,gloss,@related,@sense_id,@h_num,@parent_h_num);

-- Reindex approved matches
-- Create indices for new matches