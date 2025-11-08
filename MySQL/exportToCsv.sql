SELECT *
FROM reflex_lemma_link
INTO OUTFILE 'path/reflex_lemma_link.csv'
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' 
ESCAPED BY '\\'
ENCLOSED BY '"'
LINES TERMINATED BY '\n' ;