'''
remediation_helpers.py

A few methods to simplify CSV remediation
'''

import re
from unescape import unescape

def entry_xml(input):
    '''
    Return unescaped XML with corrected
    tag capitalization
    '''
    return re.sub(r'</?[BI]>', lambda m : m.group(0).lower(), unescape(input))

def entry_str(input): 
    '''
    Return plaintext of input (unescaped
    and tags stripped)
    '''
    return re.sub(r'</?[BIbi]>', '', unescape(input))