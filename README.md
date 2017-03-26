## Git analyser

The tool is analysing your codebase in a git repository and generating a report showing how your codebase was developing from size and complexity points of view.

## Requirements

You need to install the following python packages:

* xlsxwriter
* gitpython
* python-dateutil

## Usage

Edit the config file git_analysis.yml
Then run the script `python git_analysis.py`, it will look for the config file in the current directory. If you are working with different repositories it might make sense to create the git_analysis.yml in each of them and add it to .gitignore. And then execute the script from the respective repository directory.

## Testing

There are some unittests implemented using `unittest` in the folder test.
You may run them by executing `python -m unitest discover -v -s test` from the root folder

## Future develpment

* Optimize the code
* Make it multiprocessed and analyze complexity for different files asynchronously