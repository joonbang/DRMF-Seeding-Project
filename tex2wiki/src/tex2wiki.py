try:
    from typing import *
except ImportError:
    pass

import copy

__author__ = "Joon Bang"
__status__ = "Development"

# CONSTANTS
METADATA_TYPES = []
METADATA_MEANING = {}
label_tag = ""

# CONTAINER CLASSES
class LatexEquation(object):
    def __init__(self, label, raw_label, equation, metadata):
        self.label = label
        self.raw_label = raw_label
        self.equation = equation
        self.metadata = metadata

    def __str__(self):
        return self.label + "\n" + self.equation + "\n" + str(self.metadata)


class Section(object):
    def __init__(self, title, subsections):
        self.title = title
        self.subsections = subsections

    def __str__(self):
        result = self.title + "\n"

        if type(self.subsections) == list and len(self.subsections) and type(self.subsections[0]) == Section:
            for sub in self.subsections:
                result += str(sub) + "\n"
        else:
            result += str(self.subsections) + "\n" # str("\n".join([str(eq) for eq in self.subsections])) + "\n"

        return result


# HELPER METHODS
def find_all(pattern, string):
    # type: (str, str) -> Generator
    """Finds all instances of pattern in string."""

    i = string.find(pattern)
    while i != -1:
        yield i
        i = string.find(pattern, i + 1)


def find_end(text, left_delimiter, right_delimiter, start=0):
    # type: (str, str, str, int) -> int
    """A .find that accounts for nested delimiters."""
    net = 0  # left delimiters encountered - right delimiters encountered
    for i, ch in enumerate(text[start:]):
        if ch == left_delimiter:
            net += 1
        elif ch == right_delimiter:
            if net == 1:
                return i + start
            else:
                net -= 1

    return -1


def get_data_str(text, latex=""):
    # type: (str) -> str
    """Gets the string in between curly brackets."""
    start = text.find(latex + "{")

    if start == -1:
        return ""

    return text[start + len(latex + "{"):find_end(text, "{", "}", start)]


def get_macro_name(macro):
    # type: (str) -> str
    """Obtains the macro name."""
    macro_name = ""
    for ch in macro:
        if ch.isalpha() or ch == "\\":
            macro_name += ch
        elif ch in ["@", "{", "["]:
            break

    return macro_name


def multi_split(s, seps):
    # type: (str, list) -> list
    """Splits a string on multiple characters, specified in "seps"."""
    res = [s]
    for sep in seps:
        s, res = res, []
        for seq in s:
            res += seq.split(sep)

    return res


def remove_break(string):
    # (str) -> str
    """Removes <br /> from the end of a string."""

    while string.rstrip("\n").endswith("<br />"):
        string = string.rstrip("\n")[:-6]

    return string


# DATA EXTRACTION
def extract_equations(raw):
    equations = raw[:-1]
    for i, equation in enumerate(equations):
        # formula stuff
        try:
            raw_formula, formula = format_formula(get_data_str(equation, latex="\\formula"))
        except IndexError:  # there is no formula.
            break

        equation = equation.split("\n")

        # get metadata
        raw_metadata = ""

        j = 0
        while j < len(equation):
            if "%" in equation[j]:
                raw_metadata += equation.pop(j)[1:].strip().strip("\n") + "\n"
            else:
                j += 1

        metadata = dict()
        for data_type in METADATA_TYPES:
            temp = format_metadata(get_data_str(raw_metadata, latex="\\" + data_type)).split("\n")
            for k, line in enumerate(temp):
                if line.rstrip().endswith("&"):
                    temp[k] = line.rstrip() + "<br />"

            metadata[data_type] = "\n".join(temp)

        equations[i] = LatexEquation(formula, raw_formula, '\n'.join(equation), metadata)

    return equations


# FORMATTING METHODS
def convert_dollar_signs(string):
    # type: (str) -> str
    """Converts dollar signs to html for math mode."""
    count = 0
    result = ""
    for i, ch in enumerate(string):
        if ch == "$":
            if count % 2 == 0:
                result += "<math>{\\displaystyle "
            else:
                result += "}</math>"
            count += 1
        else:
            result += ch

    return result


def format_formula(formula):
    # type: (str) -> Tuple[List[str], Any]
    """Obtain the raw formula (the numerical values), as well as the formatted version."""
    if formula[0] == ":":  # handling for Jacobi special stuff
        return [str(int(formula[1:]))], formula[1:].zfill(2)

    formula = multi_split(formula.split("Formula:", 1)[1], [".", ":"])

    for j in [-1, -2, -3]:
        formula[j] = formula[j].zfill(2)

    raw = copy.deepcopy(formula)

    # remove any text from the raw equation
    i = 0
    while i < len(raw):
        if not raw[i].isdigit():
            raw.pop(i)
        else:
            raw[i] = str(int(raw[i]))  # removes any 0s that are present from left end.
            i += 1

    if len(formula) == 3:
        formula = formula[0] + "." + formula[1] + ":" + formula[2]
    else:
        formula = ":".join(formula[:-3]) + ":" + formula[-3] + "." + formula[-2] + ":" + formula[-1]

    return raw, formula


def format_metadata(string):
    # type: (str) -> str
    """Formats the metadata of an equation."""
    if string == "":
        return ""

    # modified convert_dollar_sign algorithm
    dollar_count = 0
    result = ""
    for i, ch in enumerate(string):
        if ch == "$":
            if dollar_count % 2 == 1:
                result += "}</math>"
            elif dollar_count > 1:
                result = result[:-1] + "<br />\n<math>{\\displaystyle "
            else:
                result += "<math>{\\displaystyle "
            dollar_count += 1
        else:
            result += ch

    return result.strip()


# WIKITEXT GENERATION HELPER METHODS
def generate_nav_bar(info):
    # type: (list) -> Tuple[Union[str, unicode], Union[str, unicode]]
    """Generates the navigation bar code for a page."""
    links = list()
    for link, text in info:
        link = link.replace("''", "")
        text = text.replace("''", "")
        links.append(generate_link(link, text))

    nav_section = generate_html("div", "<< " + links[0], options={"id": "alignleft"}, spacing=1) + "\n" + \
        generate_html("div", links[1], options={"id": "aligncenter"}, spacing=1) + "\n" + \
        generate_html("div", links[2] + " >>", options={"id": "alignright"}, spacing=1)

    header = generate_html("div", nav_section, options={"id": "drmf_head"})
    footer = generate_html("div", nav_section, options={"id": "drmf_foot"})

    return header, footer


def generate_html(tag_name, text, options=None, spacing=2):
    """
    Generates an html tag, with optional html parameters.
    When spacing = 0, there should be no spacing.
    When spacing = 1, the tag, text, and end tag are padded with spaces.
    When spacing = 2, the tag, text, and end tag are padded with newlines.
    """
    if options is None:
        options = {}

    option_text = [key + "=\"" + value + "\"" for key, value in options.iteritems()]
    result = "<" + tag_name + " " * (option_text != []) + ", ".join(option_text) + ">"

    if spacing == 2:
        result += "\n" + text + "\n</" + tag_name + ">\n"
    elif spacing == 1:
        result += " " + text + " </" + tag_name + ">"
    else:
        result += text + "</" + tag_name + ">"

    return result


def generate_math_html(text, options=None, spacing=2):
    # type: (str, dict, int) -> str
    """Special case of generate_html, where the tag is "<math>"."""
    if options is None:
        options = {}

    option_text = [key + "=\"" + value + "\"" for key, value in options.iteritems()]
    result = "<math" + " " * (option_text != []) + ", ".join(option_text) + ">"

    if spacing == 2:
        result += "{\\displaystyle \n" + text + "\n}</math>\n"
    elif spacing == 1:
        result += "{\\displaystyle " + text + "}</math>\n"
    else:
        result += "{\\displaystyle " + text + "}</math>"

    return result


def generate_link(left, right=""):
    # type: (str, str) -> str
    """Generates a MediaWiki link."""
    if right == "":
        return "[[" + left + "|" + left + "]]"

    return "[[" + left + "|" + right + "]]"


def generate_symbols_list(text, glossary):
    # type: (str, dict) -> str
    """Generates span text based on symbols present in text. Equivalent of old symbols_list module."""
    symbols = list()

    special_cases = {"&": "& : logical and<br />"}
    acknowledged = dict()
    for case in special_cases:
        acknowledged[case] = False

    for keyword in glossary:
        for index in find_all(keyword, text):
            # if the macro is present in the text
            if index != -1:
                index += len(keyword)  # now index of next character
                if index >= len(text) or not text[index].isalpha():
                    symbols.append([keyword, index])
                    break

    span_text = ""

    # code to handle special cases
    for keyword in special_cases:
        for index in find_all(keyword, text):
            if index != -1 and not acknowledged[keyword]:
                span_text += special_cases[keyword] + "\n"
                acknowledged[keyword] = True  # to prevent duplicates

    for symbol in sorted(symbols, key=lambda l: l[1]):  # sort by list index.
        symbol = symbol[0]
        links = list()
        for cell in glossary[symbol]:
            if "http://" in cell or "https://" in cell:
                links.append(cell)

        id_link = links[0]
        links = ["[" + link + " " + link + "]" for link in links]

        meaning = list(glossary[symbol][1])

        count = 0
        for i, ch in enumerate(meaning):
            if ch == "$" and count % 2 == 0:
                meaning[i] = "<math>{\\displaystyle "
                count += 1
            elif ch == "$":
                meaning[i] = "}</math>"
                count += 1

        appearance = glossary[symbol][4].strip("$")

        span_text += "<span class=\"plainlinks\">[" + id_link + " <math>{\\displaystyle " + appearance + \
                     "}</math>]</span> : " + ''.join(meaning) + " : " + " ".join(links) + "<br />\n"

    return remove_break(span_text)  # slice off the extra br and endline


# WIKITEXT GENERATION
def create_equation_list(data, title_string=""):
    # type: (Section, str) -> str
    """Creates the 'index' pages for each section. Corrected for use of Section."""
    ret = ""

    section_names = [title_string] + [section.title for section in data.subsections] + [title_string]

    # deep down, subsections is a list of LatexEquation(s)
    for i, section in enumerate(data.subsections):
        result = "drmf_bof\n'''" + section.title.replace("''", "") + "'''\n{{DISPLAYTITLE:" + section.title + "}}\n"

        # get header and footer
        center_text = (title_string + "#").replace(" ", "_") + section.title
        link_info = [[section_names[i], section_names[i]], [center_text, section_names[i + 1]],
                     [section_names[i + 2], section_names[i + 2]]]
        header, footer = generate_nav_bar(link_info)

        result += header + "\n" + equation_list_format(section)[0].rstrip("\n") + "\n" + footer + "\n" + "drmf_eof\n"

        ret += result

    # some post-processing
    ret = ret.replace("\n\n\n", "\n")

    return ret


def create_equation_pages(data, glossary, title_string):
    # type: (Section, dict) -> str
    """Creates specific pages for each formula. Corrected for use with Section."""

    formulae = [title_string] + make_formula_list(data)[0][:-1] + [title_string]

    i = 0
    pages = list()
    for j, section in enumerate(data.subsections):
        res, i = equation_page_format(section, section.title, formulae, glossary, i)
        pages += res
        i += 1

    return "\n".join(pages) + "\n"


def equation_list_format(data, depth=0):
    # type: (Section, int) -> Tuple[Union[Union[str], Any], bool]
    """Format the equations in a section into a list style."""
    
    border = "=" * (2 + int(depth >= 2))  # '==' when depth < 2; '===' when depth >= 2
    text = "%s %s %s\n\n" % (border, data.title, border)

    contains_deeper_depth = False
    metadata = list()
    
    for i, section in enumerate(data.subsections):
        if type(section) == LatexEquation:
            equation = generate_math_html(section.equation, options={"id": section.label})
            metadata = list()
            for data_type in sorted(section.metadata.keys()):
                if section.metadata[data_type] != "":
                    metadata.append(
                        generate_html("div", METADATA_MEANING[data_type] + ": " + section.metadata[data_type],
                                      options={"align": "right"}, spacing=0)
                    )

            text += equation.rstrip("\n") + "\n" * bool(len(metadata)) + "<br />\n".join(metadata) + "<br />\n"
        else:
            contains_deeper_depth = True
            temp = equation_list_format(section, depth + 1)
            text = text.rstrip("\n") + "\n\n" + temp[0]

            if depth + 1 >= 2 and i == len(data.subsections) - 1 and temp[1]:
                text = remove_break(text)

    if depth < 2 and metadata == list() and not contains_deeper_depth:
        text = remove_break(text)

    return text, metadata == list()


def equation_page_format(info, title, formulae, glossary, i=0):
    # type: (Section, str, list, dict(, int)) -> (str, int)
    """Formats equations into individual MediaWiki pages."""
    pages = list()

    if len(info.subsections) and type(info.subsections[0]) != Section:
        for eq in info.subsections:
            # get header and footer
            center_text = (title + "#" + eq.label).replace(" ", "_")
            middle = "formula in " + title

            last_index = i + 2 + int("Formula" not in formulae[i + 2])  # sets the index for the "next" link

            link_info = [[formulae[i].replace(" ", "_"), formulae[i]], [center_text, middle],
                         [formulae[last_index].replace(" ", "_"), formulae[last_index]]]
            header, footer = generate_nav_bar(link_info)

            # add title of page, navigation headers
            result = "drmf_bof\n'''Formula:" + eq.label + "'''\n{{DISPLAYTITLE:Formula:" + eq.label + "}}\n" + header \
                     + "\n<br />"

            # add formula
            result += generate_html("div", generate_math_html(eq.equation)[:-1], options={"align": "center"},
                                    spacing=0) + "\n\n"

            # add metadata
            for data_type, info in eq.metadata.iteritems():
                if info != "":
                    result += "== " + METADATA_MEANING[data_type] + " ==\n\n"
                    result += generate_html("div", info, options={"align": "left"}, spacing=0) + "<br />\n\n"

            # proof section
            result += "== Proof ==\n\nWe ask users to provide proof(s), reference(s) to proof(s), or further " \
                      "clarification on the proof(s) in this space.\n\n"

            # symbols list section
            result += "== Symbols List ==\n\n"
            result += generate_symbols_list(result, glossary) + "\n<br />\n\n"

            # bibliography section
            result += "== Bibliography==\n\n"  # TODO: Fix typo after feature parity has been met
            result += "<span class=\"plainlinks\">" \
                      "[http://homepage.tudelft.nl/11r49/askey/contents.html " \
                      "Equation in Section " + \
                      ".".join(eq.raw_label[:2]) + \
                      "]</span> of [[Bibliography#KLS|'''KLS''']].\n\n"  # Meaning? Need to check validity of this.

            # url links placeholder
            result += "== URL links ==\n\nWe ask users to provide relevant URL links in this space.\n\n"

            # end of page
            result += "<br />" + footer + "\ndrmf_eof"
            pages.append(result)

            i += 1
    else:
        for subsection in info.subsections:
            res = equation_page_format(subsection, title, formulae, glossary, i)
            pages += res[0]
            i = res[1]

    return pages, i


def make_formula_list(info, depth=0):
    # type: (Section, int) -> (str, int)
    """Generates the list of formulae contained in the file. Used for generating headers & footers."""

    formulae = list()
    if len(info.subsections) and type(info.subsections[0]) != Section:
        for eq in info.subsections:
            formulae.append("Formula:" + eq.label)
    else:
        for subsection in info.subsections:
            formulae += make_formula_list(subsection, depth + 1)[0]

    if depth < 2:
        formulae.append(info.title)

    return formulae, depth


def section_split(string, sub=0):
    # type: (str) -> Section
    """Split string into Section objects."""

    string = string.split("\\" + sub * "sub" + "section")
    
    # base case; when depth too far
    if len(string) == 1:
        title = get_data_str(string[0]).replace("$", "''")

        equations = string[0].split("\\end{equation}")
        for i, equation in enumerate(equations[:-1]):
            equations[i] = equation.split("\\begin{equation}", 1)[1].strip()

        wrapped_equations = extract_equations(equations)

        return Section(title, wrapped_equations)

    chunk_data = list()  # list of Sections

    for chunk in string[1:]:
        chunk_data.append(section_split(chunk, sub + 1))

    title = get_data_str(string[0]).replace("$", "''")

    return Section(title, chunk_data)


def load_preset(preset):
    global METADATA_TYPES
    global METADATA_MEANING
    global label_tag
    METADATA_TYPES = list(preset["metadata"])
    METADATA_MEANING = preset["metadata"]
    label_tag = preset["label_info"]["id"]
