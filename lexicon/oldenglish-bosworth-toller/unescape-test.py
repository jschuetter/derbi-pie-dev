'''
unescape-test.py
For testing escaping, because B&T txt doesn't use
standard HTML escape character :(
'''
import html

# Read file with standard escaping
with open("bosworth-toller-1989.xml", 'r') as infile: 
    with open("bt-escaped-std.xml", 'w') as outfile: 
        for line in infile: 
            outfile.write(html.unescape(line) + "\n")

