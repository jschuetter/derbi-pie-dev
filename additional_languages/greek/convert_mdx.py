from pyglossary.glossary_v2 import Glossary  # v2 API

inp = "LS_gk.mdx"
out = "LS_gk.xdxf"

g = Glossary()
g.read(inp, formatName="mdict")                 # <-- not "mdx"
g.write(out, formatName="xdxf", keep_html=True) # or "tabfile"/"json"
print("Done →", out)
