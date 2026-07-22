-- Query column names
SELECT GROUP_CONCAT(column_name ORDER BY ordinal_position)
FROM information_schema.columns
WHERE table_name = 'temp_skt_joined'
AND table_schema = 'derbi_pie_jacob';

SELECT *
FROM skt_approved_matches
ORDER BY CAST(REPLACE(parsed_id, '*', '') AS UNSIGNED)
INTO OUTFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/exports/skt_approved_matches_v1.csv'
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' 
ESCAPED BY '\\'
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n' ;

-- Query to file
SELECT parsed_id, master_id
FROM skt_approved_matches
ORDER BY CAST(REPLACE(parsed_id, '*', '') AS UNSIGNED)
INTO OUTFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/exports/skt_approved_matches.csv'
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' 
ESCAPED BY '\\'
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n' ;