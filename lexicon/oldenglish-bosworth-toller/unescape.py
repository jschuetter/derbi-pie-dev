'''
unescape-test.py
For testing escaping, because B&T txt doesn't use
standard HTML escape character :(
'''
import html, re

# Map from regex match string to replace string
escape_map = {
    # \u0301: Unicode combining acute accent
    "[Ææ](-acute;)": "\u00e6\u0301", # \u00e6: ae ligature
    "&OElig-acute;": "\u0152\u0301", # \u0152: capital OE ligature
    "&oelig-acute;": "\u0153\u0301", # \u0153: oe ligature
    "&dash-acute;": "\u0903\u0301", # \u0903: en dash
    "&([a-z])-acute;": "\\g<1>\u0301", # catchall for other 'acute' escapes

    # \u0304: combining macron
    "[Ææ](-long;)": "\u00e6\u0304",
    "&([a-zA-Z])-long;": "\\g<1>\u0304", 

    # \u0302: combining circumflex
    "[Ææ](-circ;)": "\u00e6\u0302",

    # Other diacritics
    "&([a-zA-Z])-short;": "\\g<1>\u0306", # combining breve
    "&([a-zA-Z])-odot;": "\\g<1>\u0307",  # combining dot above
    "&([a-zA-Z])-udot;": "\\g<1>\u0323",  # combining dot below
    "&([a-zA-Z])-tilde;": "\\g<1>\u0303",  # combining tilde

    # Super & subscripts
    "&t-super;" : "\u1d57",
    "&e-super;": "\u1d49",

    # (Nonstandard) stroke characters
    # d-bar & l-bar replaced with &dstrok; and &lstrok; 
    # in original XML
    "&b-bar": "\u0180",
    "&THORN-bar": "\ua764",
    "&thorn-bar": "\ua765",

    # Greek characters
    "&alpha-tonos;": "\u03ac",
    "&epsilon-tonos;": "\u03ad",
    "&eta-tonos;": "\u03ae",
    "&omicron-tonos;": "\u03cc",
    "&iota-tonos;": "\u03af",
    "&upsilon-tonos;": "\u03cd",
    "&omega-tonos;": "\u03ce",
    "&iota-oxia;": "\u1f77",
    "&iota-diar;": "\u03ca",
    "&upsilon-dasia-oxia;": "\u1f55",
    "&w-circ;": "\u0302\u03c9",

    # Runic characters
    # https://en.wikipedia.org/wiki/Anglo-Saxon_runes#Letters
    # https://en.wikipedia.org/wiki/Runic_(Unicode_block)
    "&b-rune;": "\u16d2", # beorc
    "&c-rune;": "\u16b3", # cen
    "&d-rune;": "\u16de", # daeg
    "&e-rune;": "\u16d6", # eh
    "&f-rune;": "\u16a0", # feoh
    "&i-rune;": "\u16c1", # is
    "&l-rune;": "\u16da", # lagu
    "&m-rune;": "\u16d7", # man
    "&n-rune;": "\u16be", # nyd
    "&ng-rune;": "\u16dd", # ing
    "&p-rune;": "\u16c8", # peorth
    "&u-rune;": "\u16a2", # ur
    "&w-rune;": "\u16b9", # wynn
    "&y-rune;": "\u16a3", # yr

    # Other special characters
    "&yogh;": "\u021d", # Yogh (ȝ)
    "&YOGH;": "\u021c",
    "&dash-uncertain;": "\u0903", # en dash
    "&hand;": "\u261e", # Right-pointing white hand

    # Re-escape ampersand (not allowed in XML
    " & ": " &amp; ",
    "&c": "&amp;c",
    "\[&": "[&amp;",
    ">&": ">&amp;",
}


def custom_unescape(orig_line): 
    for match, repl in escape_map.items(): 
        orig_line = re.sub(match, repl, orig_line)
    return orig_line

def unescape(orig_line):
    '''
    Perform both default HTML and custom
    entity unescaping
    '''
    std_unescape = html.unescape(orig_line)
    unescaped = custom_unescape(std_unescape)
    return unescaped

if __name__ == "__main__":
    # Read file with standard escaping
    from time import time
    print("Reading and escaping XML file")
    start_time = time()
    with open("bosworth-toller-1989.xml", 'r') as infile: 
        with open("bt-escaped-std.xml", 'w') as outfile: 
            with open("bt-escaped-custom.xml", 'w') as newfile:
                for line in infile: 
                    std_escape = html.unescape(line)
                    outfile.write(std_escape + "\n")
                    # Perform additional escaping
                    custom_ue = custom_unescape(std_escape)
                    newfile.write(custom_ue + "\n")
    print("Unescaping completed. Runtime:", time() - start_time, "s")