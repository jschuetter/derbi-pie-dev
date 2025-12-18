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
from parse_doc import OUTPUT_DIR_PFX, TOKENS_DIR, HTML_DIR

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
class IllegalArgumentError(ValueError):
    # Custom exception for handling bad CLI args
    pass
try: 
    if len(sys.argv) < 2 or (len(sys.argv) > 2 and len(sys.argv) < 4): 
        raise IllegalArgumentError("Please provide a GitHub repo path in the form 'OWNER REPO PATH'")
    owner = DEF_REPO_NAME
    repo = DEF_REPO_NAME
    path = None
    if len(sys.argv) == 4: 
        if "/" in sys.argv[1] or "/" in sys.argv[2]:
            raise IllegalArgumentError("Repo owner and repo name may not contain '/'")
        owner = sys.argv[1]
        repo = sys.argv[2]
        path = sys.argv[3]
    else: 
        path = sys.argv[1]
except IllegalArgumentError as e:
    print(e)
    print("Example: 'tesserae tesserae texts/la/vergil.aeneid'")
    sys.exit()

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

# Delete sections file if exists
filename = urls[0].split("/")[-1]
author, work, *_ = filename.split(".")
sections_path = os.path.join(OUTPUT_DIR_PFX, HTML_DIR, author, work, "sections.json")
if os.path.exists(sections_path) and os.path.isfile(sections_path):
    try:
        os.remove(sections_path)
    except OSError:
        pass

for url in urls:
    r = requests.get(url)

    filename = url.split("/")[-1]
    author, work, *_ = filename.split(".")
    # Create output dir if not exists
    output_dir = os.path.join(OUTPUT_DIR_PFX, TOKENS_DIR, author, work)
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, os.path.splitext(filename)[0]+".csv")
    print("Output location:", output_path)

    startTime = time()
    with redirect_stdout():
        parse_doc(r.text, output_path)
    print(f"Parsed {filename} in {time() - startTime} seconds.\n")