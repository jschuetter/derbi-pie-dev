SELECT * FROM lewis_short;
SELECT * FROM lex_ref_link;

# Match latin lex_ref entries to lewis_short entries
SELECT ref.lex_ref_link_id, ref.orig_lang_abbrev, ref.reflex, ls.id, ls.lemma, ls.entry
FROM lex_ref_link ref
JOIN lewis_short ls 
-- ON ref.reflex = ls.lemma
ON ref.reflex = ls.lemma 
OR ref.reflex LIKE CONCAT(ls.lemma, ',')
WHERE ref.orig_lang_abbrev LIKE '%lat%';

SELECT COUNT(*)
FROM lex_ref_link ref
JOIN lewis_short ls
ON ref.reflex = ls.lemma
WHERE ref.orig_lang_abbrev LIKE '%lat%';

SELECT COUNT(*)
FROM lex_ref_link
WHERE orig_lang_abbrev='lat.';

SELECT * FROM 