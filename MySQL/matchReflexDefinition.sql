SELECT * FROM lewis_short;
SELECT * FROM lex_ref_link;

# Match latin lex_ref entries to lewis_short entries
SELECT ref.lex_ref_link_id, ref.orig_lang_abbrev, ref.reflex, ls.id, ls.lemma, ls.entry
FROM lex_ref_link ref
JOIN lewis_short ls 
-- ON ref.reflex = ls.lemma
ON REPLACE(
	REPLACE(
		REPLACE(ref.reflex, 'v', 'u'),
			'j', 'i'),
				'-', '') 
	= REPLACE(
		REPLACE(ls.lemma, 'v', 'u'),
			'j', 'i')
OR REPLACE(
	REPLACE(
		REPLACE(ref.reflex, 'v', 'u'),
			'j', 'i'),
				'-', '') 
	LIKE CONCAT(
		REPLACE(
			REPLACE(ls.lemma, 'v', 'u'),
				'j', 'i'), ',%')
WHERE ref.orig_lang_abbrev LIKE '%lat%';

SELECT COUNT(*)
FROM lex_ref_link ref
JOIN lewis_short ls
ON ref.reflex = ls.lemma
WHERE ref.orig_lang_abbrev LIKE '%lat%';

SELECT COUNT(*)
FROM lex_ref_link
WHERE orig_lang_abbrev='lat.';