CREATE DATABASE derbi_pie_sql;
USE derbi_pie_sql;
CREATE TABLE lewis_short (
	id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    lemma TEXT NOT NULL,
    type TEXT NOT NULL,
    orthography TEXT,
    pos TEXT,
    etymology TEXT,
    entry MEDIUMTEXT
);
# Load data from CSV
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/lewis-short.csv'
INTO TABLE lewis_short
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(lemma, type, orthography, pos, etymology, entry);