'''
unescape-test.py
For testing escaping, because B&T txt doesn't use
standard HTML escape character :(
'''
import html, re

# Map from regex match string to replace string
escape_map = {
    # \u0301: Unicode combining acute accent
    "[Ææ](-acute;)": "\u0301",
    "&oelig-acute;": "\u0153\u0301", # \u0153: oe ligature
    "&dash-acute;": "\u0903\u0301", # \u0903: en dash
    "&([a-z])-acute;": "\\g<1>\u0301", # catchall for other 'acute' escapes

    # \u0304: combining macron
    "[Ææ](-long;)": "\u0304",
    "&([a-z])-long;": "\\g<1>\u0304", 

    # \u0306: combining breve
    "&([a-z])-short;": "\\g<1>\u0306", 

    "[Ææ](-circ;)": "\u0302",  # \u0302: combining circumflex accent

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

    # Other special characters
    "&yogh;": "\u021d",
    "&YOGH;": "\u021c",
}


def custom_unescape(orig_line): 
    for match, repl in escape_map: 
        orig_line = re.sub(match, repl, orig_line)
    return orig_line

# Read file with standard escaping
with open("bosworth-toller-1989.xml", 'r') as infile: 
    with open("bt-escaped-std.xml", 'w') as outfile: 
        with open("bt-escaped-custom.xml", 'w') as newfile:
            for line in infile: 
                std_escape = html.unescape(line)
                outfile.write(std_escape + "\n")
                # Perform additional escaping
                custom_ue = custom_unescape(std_escape)
                newfile.write(custom_ue + "\n")