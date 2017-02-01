# Maple CFSF Seeding Project
This project uses Python to convert the continued fractions for special functions library, written in Maple, into LaTeX. 

## Prerequisites
This program requires Python 2.6+ to run.

The program also relies on multiple files in order to run, containing key information for translation.

1. A `data` folder, containing two files: `keys.json` and `section_names`.
   By default, this folder and the aforementioned files are included with the translator.
   Modifications may be made to this file, at your own risk.
2. An `out` folder, containing a file called `primer`. `primer` is used in the generation of an output file,
   as the beginning text to the file; this usually contains different settings for the `.tex` file, and the
   `\begin{document}` statement. This is NOT included by default.

Please ensure that these folders are located within the `maple2latex` directory.


## Usage
To run the program, ensure that you are in the directory where maple2latex is located. Then, run the command `python maple2latex/src/main.py`.

~~Currently, the program translates only the CFSF library of functions. In the future, support will be added for
translating individual .mpl files.~~

Currently, the program is able to translate the CFSF library of functions. It also supports single-equation translation.

To translate a directory of files, run `main.py` with the argument `-dt`, and include the directory of files and the output file as arguments.
This may not work properly with non-CFSF directories.

**WARNING, EXPERIMENTAL FEATURE:**

To activate single-equation translate mode, run `main.py` with the argument `-et` (see above command).


### Input Formatting
Please ensure that the Maple equation is staggered into several lines, with a field per line and a comma delimiter.
The equation should end with the `):` delimiter.

Supported fields include:
```
begin
booklabelv1
booklabelv2
category
constraints
even
factor
front
general
lhs
odd
parameters
```

#### Example Equation

```
create( 'sample type',
  label = "sample label",
  booklabelv1 = "book label v1",
  factor = ...,
  general = ...,
  parameters = ...,
  constraints = ...,
  function = ...,
  lhs = ...,
  category = "sample category"
):
```


## Code Explanation
There are three files, `main.py`, `maple_tokenize.py`, and `translator.py`. The bulk of the code is located in `translator.py.`

The program works by parsing through "tokens," which are created by running the `tokenize` function on a string. 
It then goes through the tokens, joining them when necessary. It initially joins terms grouped in parentheses, starting from 
the innermost set of parentheses and working its way outwards. It has separate functions handling translation of mathematical 
functions, and basic operations (addition, multiplication, division, etc.). 
