'''
resolve_multiple_auto.py

Script for automatically matching parsed lemmas which
matched multiple lemmas in lex_master.

Approach: 
- Check Levenshtein distance with each 'master_resolved' string.
    - If any found > 85, auto-approve
    - If one found in (60,85], or multiple > 60, mark for manual approval
    - If none found > 50, discard for new indexing
'''

