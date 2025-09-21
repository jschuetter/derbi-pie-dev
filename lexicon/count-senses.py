'''
Script for counting max # of <sense> tags in a single entry
'''
import re

pattern = re.compile(r'<sense\b')
max_matches = 0
max_line = None

with open('lewis-short.xml', 'r', encoding='utf-8') as f: 
    for line in f: 
        matches = pattern.findall(line)
        count = len(matches)
        if count > max_matches:
            max_matches = count
            max_line = line

output_file = "sense-count.txt"
with open(output_file, 'w') as f_out:
    f_out.write(f"Max tags: {max_matches}\n")
    f_out.write(f"Line: {max_line}\n")
