SELECT ref.reflex, ref.gloss_orig, ls.lemma, ls.entry_str, ls2.entry_str
FROM lex_ref_link ref
JOIN reflex_lemma_link lnk
ON ref.lex_ref_link_id = lnk.lex_ref_link_id
JOIN lewis_short ls
ON ls.lemma_id = lnk.lewis_short_id
LEFT JOIN lewis_short ls2
-- ON SUBSTRING(ls.child_ids, 1, LOCATE(',', ls.child_ids)) = ls2.entry_id
ON ls.child_ids = ls2.entry_id
WHERE ls.`type` != 'sense'
LIMIT 10000;