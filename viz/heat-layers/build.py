import re
t=open("viz/heat-layers/template.html",encoding="utf-8").read().replace("__DATA__",open("viz/heat-layers/data.json").read())
parts=re.split(r"(<script\b[^>]*>.*?</script>)",t,flags=re.S)
out="".join(("".join(c if ord(c)<128 else "\\u%04x"%ord(c) for c in p)) if p.startswith("<script") else ("".join(c if ord(c)<128 else "&#%d;"%ord(c) for c in p)) for p in parts)
open("viz/heat-layers/heat-layers.html","w",encoding="ascii").write(out)
