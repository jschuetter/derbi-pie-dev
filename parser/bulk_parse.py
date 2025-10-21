'''
bulk-parse.py
21 October 2025

Accepts a GitHub repo path (in form 'OWNER REPO PATH')
and parses all documents found therein.
Raises ValueError if documents are not in .tess format.
'''

from parse_doc import parse_doc
from contextlib import contextmanager
from time import time
import requests, sys, os, re

OUTPUT_DIR_PFX = "../corpus/parsed/"
DEF_REPO_NAME = "tesserae" # Autofill Tesserae repo name if not provided

#region context-manager
# Context manager to suppress CLTK default output
# SOURCE: https://thesmithfam.org/blog/2012/10/25/temporarily-suppress-console-output-in-python/
# Minor modifications made
@contextmanager
def redirect_stdout(redirect = os.devnull):
    with open(redirect, "w") as rd:
        old_stdout = sys.stdout
        sys.stdout = rd
        try:
            yield
        finally:
            sys.stdout = old_stdout
#endregion

# Request data from GH
if len(sys.argv) < 2 or (len(sys.argv) > 2 and len(sys.argv) < 4): 
    raise ValueError("Please provide a GitHub repo path in the form 'OWNER REPO PATH'")
owner = DEF_REPO_NAME
repo = DEF_REPO_NAME
path = None
if len(sys.argv) == 4: 
    if "/" in sys.argv[1] or "/" in sys.argv[2]:
        raise ValueError("Repo owner and repo name may not contain '/'")
    owner = sys.argv[1]
    repo = sys.argv[2]
    path = sys.argv[3]
else: 
    path = sys.argv[1]

headers = {
    "Accept": "application/vnd.github.object",
    "X-GitHub-Api-Version": "2022-11-28"
}
r = requests.get(f"https://api.github.com/repos/{owner}/{repo}/contents/{path}", headers=headers)
res = r.json()
urls = []
if "entries" in res:
    for e in res["entries"]:
        urls.append(e["download_url"])
else: 
    urls.append(res["download_url"])

print("Discovered files:\n", "\n".join(urls), "\n")

for url in urls:
    r = requests.get(url)

    # Parse output file from filename
    filename = url.split("/")[-1]
    author, work, *_ = filename.split(".")
    outputDir = os.path.join(OUTPUT_DIR_PFX, author, work)
    outputFile = os.path.join(outputDir, filename.rstrip(".tess") + ".csv")
    # Create output dir if not exists
    os.makedirs(outputDir, exist_ok=True)
    print("Output file:", outputFile)

    clean_text = re.sub(r'^\<[ a-zA-Z0-9.]*\>\s', '', r.text, flags=re.MULTILINE)

    startTime = time()
    with redirect_stdout():
        parse_doc(clean_text, outputFile)
    print(f"Parsed {filename} in {time() - startTime} seconds.\n")