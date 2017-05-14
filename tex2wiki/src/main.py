import csv
import sys
import tex2wiki

__author__ = "Joon Bang"
__status__ = "Development"

# CONSTANTS
GLOSSARY_LOCATION = "tex2wiki/data/new.Glossary.csv"


def usage():
    print "Usage: python tex2wiki.py filename(s) ...\nNote: filename(s) should NOT include their extensions."
    sys.exit(0)


def main(input_file, output_file, title):
    # (str, str, str) -> None
    """Converts a .tex file to MediaWiki page(s)."""

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
    if len(sys.argv) < 2:
        usage()

    for i, filename in enumerate(sys.argv[1:]):
        main(
            input_file=filename + ".tex",
            output_file=filename + ".mmd",
            title="Orthogonal Polynomials"
        )
