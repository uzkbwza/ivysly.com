import re
import os

def replace_footnotes(string):
    replaced_top_fns = re.sub(r'(\[)(\d+)(\*\])', r'<a href="#fn\2" id="ref\2"><sup>[\2]</sup></a>', string)
    replaced_bottom_fns = re.sub(r'(\[\*)(\d+)(\])', r'<a href="#ref\2" id="fn\2"><sup>[\2]</sup></a>', replaced_top_fns)
    return replaced_bottom_fns

def main():
    os.chdir("pelican/content/")
    entries = os.listdir(".")
    for e in entries:
        if e.split(".")[-1] == "md":
            formatted = ""
            with open(e, "r") as f:
                formatted = replace_footnotes(f.read())
            with open(e, "w") as f:
                f.write(formatted)

if __name__ == "__main__":
    main()
