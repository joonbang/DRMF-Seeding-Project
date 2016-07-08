#!/usr/bin/env python

import tokenize
from StringIO import StringIO

def key_info(filename):
    return [line.split(" || ", 1) for line in open(filename).read().split("\n")
                 if line != "" and "%" not in line]

functions = key_info("keys/functions")
symbols = key_info("keys/symbols")
constraints = key_info("keys/constraints") + [["::", "\\in "]]

special = {"(": "\\left(", ")": "\\right)", "+-": "-", "\\subplus-": "-", "^{1}": "", "\\inNot": "\\notin"}
brackets = {"[": "", "]": ""}

alphabet = "abcdefghijklmnopqrstuvwxyz"

def sort(li):
    organized = dict()

    for s in li:
        num = s.split("\n")[0][22:-1]

        for i, ch in enumerate(alphabet):
            num = num.replace(ch, "."+str(i + 1))

        num = [n.rjust(3) for n in num.split(".")]

        organized[''.join(num)] = [num, s]

    return [organized[''.join(id)][1] for id in sorted([organized[q][0] for q in organized])]

def find(li, element):
    for group in li:
        if group[0] == element:
            return group[1]

    return element

def replace_strings(string, li):
    """
    Replaces multiple strings with multiple other strings, stored in lists of length two in li.
    The first element is the string to find, and the second element is the replacement string.
    A dictionary can also be given.
    """

    if type(li) == dict:
        for key in list(li):
            string = string.replace(key, li[key])

    elif type(li) == list:
        for key in li:
            string = string.replace(key[0], key[1])

    else:
        raise TypeError("Type of given key set is incorrect.")

    return string

def parse_brackets(string):
    """
    Obtains the contents from data encapsulated in squar ebrackets
    """

    string = string[1:-1].split(",")
    for i, e in enumerate(string):
        string[i] = replace_strings(e, brackets).strip()

    i = 0
    while i + 1 < len(string):
        string[i] = [string[i], string.pop(i+1)]
        i += 1

    return string

def trim_parens(exp):
    """
    Removes unnecessary parentheses
    """

    if exp == "":
        return ""

    # checks whether the outer set of parentheses are necessary
    if exp[0] == "(" and exp[-1] == ")":
        test = exp[1:-1]

        # validate whether test is correct (in terms of parentheses)
        s = list()  # stack
        for ch in test:
            if ch == "(":
                s.append(ch)
            elif ch == ")":
                if len(s) == 0:
                    return exp
                else:
                    s.pop()

        if len(s) != 0:
            return exp

        return test

    return exp

def make_frac(parts):
    """
    Generate a LaTeX frac from its parts [numerator, denominator]
    """

    return translate("(" + parts[0] + ") / (" + parts[1] + ")")

def basic_translate(exp):
    """
    Translates basic mathematical operations (does not include functions)
    Does not translate parentheses
    """

    for order in xrange(3):
        i = 0
        while i < len(exp):
            modified = False

            if exp[i] == "I":
                exp[i] = "i"

            elif exp[i] == "!" and order == 0:
                exp[i - 1] += "!"
                modified = True

            elif exp[i] == "^" and order == 0:
                power = trim_parens(exp.pop(i + 1))
                exp[i - 1] += "^{%s}" % power
                modified = True

            elif exp[i] == "*" and order == 1:
                if "\\" in exp[i - 1] and exp[i + 1][0] != "\\":
                    exp[i - 1] += " "

                exp[i - 1] += exp.pop(i + 1)
                modified = True

            elif exp[i] == "/" and order == 1:
                for index in [i - 1, i + 1]:
                    exp[index] = trim_parens(exp[index])
                exp[i - 1] = "\\frac{%s}{%s}" % (exp[i - 1], exp.pop(i + 1))
                modified = True

            if modified:
                exp.pop(i)
                i -= 1
            else:
                i += 1

    return ''.join(exp)

def count_args(string, pattern):
    if string == "":
        return 0
    return string.count(pattern) + 1

def get_arguments(function, string):
    """
    Obtains the arguments of a function
    """

    if string == ["(", ")"]:
        return []

    elif function in ["hypergeom", "qhyper"]:
        args = [basic_translate(replace_strings(s, brackets).split()) for s in ' '.join(string[1:-1]).split("] , ")]

        if function == "qhyper":
            args += args.pop(2).split(",")

        args = [str(count_args(args[i], ",")) for i in [0, 1]] + args

    elif function == "sum":
        args = basic_translate(string[1:-1]).split(",")
        args = args.pop(1).split("..") + [args[0]]
        if args[1] == "infinity":
            args[1] = "\\infty"

        args[0] = args[0].replace("i", "k")

    elif function == "log[q]":
        args = ["q"] + basic_translate(string[1:-1]).split(",")

    else:
        args = basic_translate(string[1:-1]).split(",")

    return args

def generate_function(name, args):
    """
    Generate a function with the provided name and arguments
    """

    # special parsing of arguments, based on the function
    # (i.e. if information needs to be extrapolated) from the data

    result = list()
    for group in functions:
        if group[0] == name and len(args) + 1 == len(group[1].split(" || ")):
            result = group[1].split(" || ")
            break

    for n in xrange(1, len(result)):
        result.insert(2 * n - 1, args[n - 1])

    return ''.join(result)

def translate(exp):
    """
    Translate a segment of Maple to LaTeX, including functions
    """

    if exp == "":
        return ""

    exp = replace_strings(exp.strip(), constraints)
    exp = replace_strings(exp, {"functions:-": ""})

    s = list()
    def add_to_list(a, b, c, d, e):
        s.append(b)

    tokenize.tokenize(StringIO(exp).readline, add_to_list)

    exp = s

    # exp = replace_strings(exp, spacing).split()

    # print exp

    for i in xrange(len(exp)):
        exp[i] = find(symbols, exp[i])

    for i in xrange(len(exp)-1, -1, -1):
        if exp[i] == "(":
            r = i + exp[i:].index(")")
            piece = exp[i:r + 1]

            if exp[i - 1] == "]":
                sq = i - 2 - exp[:i - 1][::-1].index("[")
                piece = [piece[0]] + exp[sq + 1:i - 1] + [","] + piece[1:]
                i = sq

            if find(functions, exp[i - 1]) != exp[i - 1]:
                i -= 1
                piece = generate_function(exp[i], get_arguments(exp[i], piece))
            else:
                piece = basic_translate(piece)

            if "frac" in replace_strings(piece, {"(": ""})[:6] and (r + 2 > len(exp) or exp[r + 1] != "^"):
                while piece != trim_parens(piece):
                    piece = trim_parens(piece)

            exp = exp[0:i] + [piece] + exp[r + 1:]

    return basic_translate(exp)

def modify_fields(eq):
    eq.lhs = translate(eq.lhs)
    eq.factor = translate(eq.fields["factor"])
    eq.front = translate(eq.fields["front"])

    if eq.eq_type == "series":
        eq.general = translate(eq.general[0])

    elif eq.eq_type == "contfrac":
        eq.general = parse_brackets(eq.general[0])[0]

        if eq.begin != "":
            eq.begin = parse_brackets(eq.begin)

def make_equation(eq):
    """
    Make a LaTeX equation based on a MapleEquation object
    """

    modify_fields(eq)

    equation = "\\begin{equation*}\\tag{%s}\n  %s\n  = " % (eq.label, eq.lhs)

    if eq.factor == "1":
        eq.factor = ""

    # translates the Maple information (with spacing)
    if eq.eq_type == "series":
        if eq.factor != "":
            equation += eq.factor + " "

        elif eq.front != "":
            equation += eq.front + "+"

        equation += "\\sum_{k=0}^\\infty "

        if eq.category == "power series":
            equation += eq.general
        elif eq.category == "asymptotic series":  # make sure to fix asymptotic series
            equation += "(" + eq.general + ")"

    elif eq.eq_type == "contfrac":
        start = 1  # in case the value of start isn't assigned

        if eq.front != "":
            equation += eq.front + "+"
            start = 1

        if eq.begin != "":
            for piece in eq.begin:
                equation += make_frac(piece) + " \\subplus "
                start += 1

        if eq.factor != "":
            if eq.factor == "-1":
                equation += "-"
            else:
                equation += eq.factor + " "

        if eq.general != ["0", "1"]:
            equation += "\\CFK{m}{%s}{\\infty}@@{%s}{%s}" % (str(start), trim_parens(translate(eq.general[0])),
                                                             trim_parens(translate(eq.general[1])))
        else:
            equation += "\\dots"

    # adds metadata
    view_metadata = True

    if view_metadata:
        equation += "\n\\end{equation*}\n$$%s$$\n\\begin{center}%s\\end{center}" % (
            translate(eq.constraints), eq.category)
    else:
        equation += "\n  %  \\constraint{$" + translate(eq.constraints) + "$}"
        equation += "\n  %  \\category{" + eq.category + "}"
        equation += "\n\\end{equation*}"

    return replace_strings(equation, special)
