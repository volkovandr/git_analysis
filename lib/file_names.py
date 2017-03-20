#!/usr/bin/python3
'''Functions performing operations on names of files'''


import re


def process_renamed_file(filename):
    '''Processes renamed files in git
    Takes filename that may have a format /path/{old_name => new_name}
    Returns a tuple ('/path/old_name', '/path/new_name')
    When no renaming happened then both old and new names are set to
    the same values
    '''
    re_match_simple = re.search("^(?P<old>.+)( => )(?P<new>.+)$", filename)
    if not re.search(".+ => .+", filename):
        return filename, filename
    re_match_curly = re.search(
        "(?P<before>.*)(\{)(?P<old>.+)( => )(?P<new>.+)(\})(?P<after>.*)",
        filename)
    if re_match_curly:
        match = re_match_curly
        before = match.group("before")
        after = match.group("after")
    else:
        match = re_match_simple
        before = ""
        after = ""
    old = match.group("old")
    new = match.group("new")
    return (
        "{}{}{}".format(before, old, after),
        "{}{}{}".format(before, new, after))


def ignore_file(filename, ignored_files):
    if not filename:
        return None
    for ignore_pattern in ignored_files:
        if re.search(ignore_pattern, filename):
            return True
