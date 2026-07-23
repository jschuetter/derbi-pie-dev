'''
match_utils.py

A script containing helper functions for matching parsed
lemmas with lex_master lemmas.
'''
import sys
import termios, tty

FIELDNAMES = ["lex_ref_link_id","reflex","gloss_eng","lemma_id","lemma","gloss","entry_str"]

def getch():
    '''Helper function to capture a single char from terminal input'''
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)              # raw mode: no line buffering
        ch = sys.stdin.read(1)    # read one byte
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)