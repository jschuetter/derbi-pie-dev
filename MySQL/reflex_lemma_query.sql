SELECT ref.reflex, ref.gloss_orig, ls.lemma, ls.entry_str
FROM lex_ref_link ref
JOIN reflex_lemma_link lnk
ON ref.lex_ref_link_id = lnk.lex_ref_link_id
JOIN lewis_short ls
ON ls.lemma_id = lnk.lewis_short_id
WHERE ls.parent_id IS NULL
LIMIT 10000;