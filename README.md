## Git analyser

The tool is analysing your codebase in a git repository and generating a report showing how your codebase was developing from size and complexity points of view.

## Requirements

You need to install the following python packages:

* xlsxwriter
* gitpython

## Usage

Edit the file git_analysis.py and add the path to the repository and the list of the files that should be exluded from the analysis and the name of the report file in the lines 13-16
Then run the script `python git_analysis.py`
