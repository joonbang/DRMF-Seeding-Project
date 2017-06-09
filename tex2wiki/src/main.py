import csv
import sys
import tex2wiki
import json

__author__ = "Joon Bang"
__status__ = "Development"

# CONSTANTS
GLOSSARY_LOCATION = "tex2wiki/data/new.Glossary.csv"


def usage():
    print "Usage: python tex2wiki.py filename preset\nNote: filename should NOT include their extensions."
    sys.exit(0)


def main(input_file, output_file, title, preset):
    # (str, str, str) -> None
    """Converts a .tex file to MediaWiki page(s)."""
    
    tex2wiki.load_preset(preset)

    with open(input_file) as f:
        text = f.read()

    glossary = dict()
    with open(GLOSSARY_LOCATION, "rb") as csv_file:
        glossary_file = csv.reader(csv_file, delimiter=',', quotechar='\"')
        for row in glossary_file:
            glossary[tex2wiki.get_macro_name(row[0])] = row

    text = text.split("\\begin{document}", 1)[1]

    info = tex2wiki.section_split(text)  # creates tree, split into section, subsection, subsubsection, etc.
    
    output = tex2wiki.create_equation_list(info, title) + tex2wiki.create_equation_pages(info, glossary, title)
    output = output.replace("<br /><br />", "<br />")

    with open(output_file, "w") as f:
        f.write(output)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        usage()
    
    presets = json.loads(open("tex2wiki/presets.json").read())
    
    if sys.argv[2] not in presets.keys():
        print "Error: that preset does not exist."
        sys.exit(0)
    
    preset = presets[sys.argv[2]]
    
    main(
        input_file=sys.argv[1] + ".tex",
        output_file=sys.argv[1] + ".mmd",
        title=preset["title"],
        preset=preset
    )
