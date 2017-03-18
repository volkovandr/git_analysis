## Git analyser

The tool is analysing your codebase in a git repository and generating a report showing how your codebase was developing from size and complexity points of view.

## Requirements

You need to install the following python packages:

* xlsxwriter
* gitpython

## Usage

Edit the config file git_analysis.yml
Then run the script `python git_analysis.py`, it will look for the config file in the current directory. If you are working with different repositories it might make sense to create the git_analysis.yml in each of them and add it to .gitignore. And then execute the script from the respective repository directory.

## Future develpment

* Refactor the code: remove unused code
* In the excel report: add for each file a brief hisory of the last 5 revisions: number of lines of code and complexity metric
