#!/usr/bin/python3


from git import Repo
from git.exc import InvalidGitRepositoryError

import datetime
import re
from math import sqrt
from itertools import zip_longest
import sys
import yaml


path = ''
ignored_files = []
xlsx_report = ''
ignore_one_char_lines = True


def load_settings():
    settings_file = 'git_analysis.yml'
    global path
    global ignored_files
    global xlsx_report
    with open(settings_file) as yml_file:
        try:
            file_data = yaml.load(yml_file)
            path = file_data["path"]
            ignored_files = file_data["ignored_files"]
            xlsx_report = file_data["report"]
        except yaml.YAMLError as e:
            print("Cannot parse the settings file {}: {}".format(
                settings_file, str(e)))
            exit(1)
        except KeyError as e:
            print("Cannot find a required config parameter", str(e))


def import_repo(path):
    try:
        return Repo(path)
    except InvalidGitRepositoryError as e:
        print("Invalid git repository {}".format(
            str(e)))
        exit(1)


def print_config(repo):
    print("Current config:")
    reader = repo.config_reader()
    for section in reader.sections():
        for option in reader.options(section):
            print("  {}.{} = {}".format(
                section, option, reader.get_value(section, option)))


def print_branches(repo):
    print("Branches:")
    for head in repo.heads:
        print("  {}".format(head))
    print("Current branch:", repo.head.reference)


def print_commits(repo, print_files):
    for commit in repo.iter_commits():
        print("Commit: {}".format(commit))
        print("  Commit date: {}".format(
            datetime.datetime.fromtimestamp(
                commit.committed_date
            ).strftime('%Y-%m-%d %H:%M:%S')))
        print("  Author: {}".format(commit.author))
        print("  Summary: {}".format(commit.summary))
        print("  Stats: {}".format(commit.stats.total))
        if print_files:
            print("  {:80} {:>5} {:>5} {:>5}".format(
                "Files:", "ins", "dels", "lines"))
            file_stats = commit.stats.files
            for file in file_stats:
                stats = file_stats[file]
                inss = stats["insertions"]
                dels = stats["deletions"]
                lins = stats["lines"]
                print("    {:78} {:>5} {:>5} {:>5}".format(
                    file, inss, dels, lins))


def process_renamed_file(filename):
    '''Processes renamed files in git
    Takes filename that may have a format /path/{old_name => new_name}
    Returns a tuple ('/path/old_name', '/path/new_name')
    When no renaming happened then both old and new names are set to
    the same values
    '''
    re_match_simple = re.search(
        "^(?P<old>.+)( => )(?P<new>.+)$",
        filename)
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
    return ("{}{}{}".format(before, old, after),
            "{}{}{}".format(before, new, after))


def ignore_file(filename):
    for ignore_pattern in ignored_files:
        if re.search(ignore_pattern, filename):
            return True
    return False


def collect_stats_per_file(repo):
    print("Collecting file statistics")
    files = {}
    for commit in repo.iter_commits():
        print(".", end="")
        sys.stdout.flush()
        tree_info = collect_complexity_stats_from_file_tree(commit.tree)
        file_stats = commit.stats.files
        for file in file_stats:
            old_name, new_name = process_renamed_file(file)
            if ignore_file(old_name) or ignore_file(new_name):
                continue
            stats = file_stats[file]
            if new_name not in files:
                files[old_name] = {"commits": 0, "lines": 0, "insertions": 0,
                                   "deletions": 0, "deleted": False,
                                   "name": new_name, "complexity": []}
            if old_name != new_name and new_name in files:
                files[old_name] = files[new_name]
                del files[new_name]
            files[old_name]["commits"] = files[old_name]["commits"] + 1
            files[old_name]["lines"] = files[old_name]["lines"] + \
                stats["lines"]
            files[old_name]["insertions"] = files[old_name]["insertions"] + \
                stats["insertions"]
            files[old_name]["deletions"] = files[old_name]["deletions"] + \
                stats["deletions"]
            if stats["deletions"] == stats["lines"] and stats["lines"] > 0:
                files[old_name]["deleted"] = True
            else:
                files[old_name]["complexity"].append({
                    "commit": str(commit),
                    "stats": get_stats_for_file(tree_info, new_name)})
    print("Done")
    return files


def print_file_stats(files, print_deleted):
    print(
        "{:50} {:50} {:8} {:8} {:5} {:5} {:5} {:5} {:5} {:4} {:4} {:4}"
        .format("Recent name", "Original name", "deleted", "revisions", "ins",
                "dels", "lines", "lines", "code", "avg", "dev", "max"))
    for file in sorted([(files[file]["name"], file) for file in files]):
        file_data = files[file[1]]
        if file_data["deleted"] and not print_deleted:
            continue
        complexity_stats = file_data["complexity"][0]["stats"]
        complexity_str = "{:>5} {:>5} {:>4} {:>4} {:>4}".format(
            complexity_stats["lines total"],
            complexity_stats["lines code"],
            round(complexity_stats["stats"]["avg"], 2)
            if complexity_stats["stats"]["avg"] else "",
            round(complexity_stats["stats"]["stddev"], 2)
            if complexity_stats["stats"]["stddev"] else "",
            complexity_stats["stats"]["max"])
        print("{:50} {:50} {:8} {:8} {:5} {:5} {:5} {}".format(
            file[0],
            file[1] if file[0] != file[1] else "",
            "yes" if file_data["deleted"] else "",
            file_data["commits"],
            file_data["insertions"],
            file_data["deletions"],
            file_data["lines"],
            complexity_str))


def process_indent_stats(indent_stats):
    cnt = sum(indent_stats)
    sum_ = sum([(i + 1) * indent_stats[i] for i in range(len(indent_stats))])
    if cnt == 0:
        avg = None
    else:
        avg = sum_ / float(cnt)
    max_ = len(indent_stats)
    if sum_ > 0:
        stddev = sqrt(sum(
            [((i + 1 - avg) ** 2) * indent_stats[i]
             for i in range(len(indent_stats))]) / cnt)
    else:
        stddev = None
    return {
        "avg": avg,
        "sum": sum_,
        "cnt": cnt,
        "max": max_,
        "stddev": stddev,
        "hist": indent_stats
    }


def analyze_complexity(blob):
    def remove_python_docstring(lines):
        result = []
        wait_for_docstring = True
        in_docstring = False
        for line in lines:
            if wait_for_docstring and line.startswith('#!'):
                continue
            if wait_for_docstring and (line.strip().startswith("'''") or
                                       line.strip().startswith('"""')):
                in_docstring = True
                wait_for_docstring = False
                if line.strip() == "'''" or line.strip() == '"""':
                    continue
            if in_docstring and (line.strip().endswith("'''") or
                                 line.strip().endswith('"""')):
                in_docstring = False
                continue
            if in_docstring:
                continue
            result.append(line)
            if (line.strip().startswith('def ') or
                    line.strip().startswith("class ")):
                wait_for_docstring = True
        return result

    lines = blob.data_stream.read().decode().split('\n')
    lines_filtered = [l for l in lines if len(l.strip()) > (
        1 if ignore_one_char_lines else 0)]
    if blob.mime_type == 'text/x-python':
        lines_filtered = remove_python_docstring(lines_filtered)
    indent_stats = {}
    for l in lines_filtered:
        indent = len(l) - len(l.lstrip())
        if indent not in indent_stats:
            indent_stats[indent] = 1
        else:
            indent_stats[indent] = indent_stats[indent] + 1
    indents = [k for k in indent_stats]
    indents.sort()
    indent_stats = [indent_stats[i] for i in indents]
    return {"lines total": len(lines), "lines code": len(lines_filtered),
            "stats": process_indent_stats(indent_stats)}


def collect_complexity_stats_from_file_tree(tree):
    result = []
    for item in tree:
        if type(item).__name__ == 'Blob':
            if ignore_file(item.path):
                continue
            result.append({
                "path": item.path,
                "size": item.size,
                "mime_type": item.mime_type,
                "complexity": analyze_complexity(item)})
        elif type(item).__name__ == 'Tree':
            result = result + collect_complexity_stats_from_file_tree(item)
        else:
            print("Dont know how to work with type", type(item).__name__)
    return result


def get_stats_for_file(tree_info, file):
    for tree_item in tree_info:
        if tree_item["path"] == file:
            return tree_item["complexity"]
    print("Cannot find file {} in the list {}".format(
        file, [item["path"] for item in tree_info]))


def join_histogram(a, b):
    return [
        (a if a is not None else 0) + (b if b is not None else 0)
        for (a, b) in zip_longest(a, b)]


def collect_stats_per_commit(repo):
    print("Collecting complexity statistics for each revision")
    result = []
    for commit in repo.iter_commits():
        print(".", end="")
        sys.stdout.flush()
        tree_info = collect_complexity_stats_from_file_tree(commit.tree)
        indent_hist = []
        for tree_item in tree_info:
            # print(tree_item)
            indent_hist = join_histogram(
                indent_hist, tree_item["complexity"]["stats"]["hist"])
        stats = process_indent_stats(indent_hist)
        result.append(
            {"commit": str(commit), "stats": stats,
             "date": datetime.datetime.fromtimestamp(
                commit.committed_date).strftime('%Y-%m-%d %H:%M:%S')})
    print("Done")
    return result


def print_commit_stats(commit_stats):
    print("{:40} {:>6} {:>4} {:>4} {:>4}".format(
        "commit", "lines", "avg", "sdev", "max"))
    for stats_item in commit_stats:
        stats = stats_item["stats"]
        commit = stats_item["commit"]
        print("{:40} {:>6} {:>4} {:>4} {:>4}".format(
            str(commit), stats["cnt"], round(stats["avg"], 2),
            round(stats["stddev"], 2), stats["max"]))


def create_xlsx_report(xlsx_file, commit_stats, file_stats):
    print('Writing Excel report...')
    import os.path
    from os import remove
    if os.path.isfile(xlsx_file):
        try:
            remove(xlsx_file)
        except:
            print("The file {} cannot be removed. Already in use?".format(
                xlsx_file))
            return False
    import xlsxwriter
    workbook = xlsxwriter.Workbook(xlsx_file)
    commit_stat_sheet = workbook.add_worksheet("commits")

    header_format = workbook.add_format({"bold": True})
    indent_format = workbook.add_format({"num_format": "#,##0.000"})

    commit_stat_sheet.write(0, 0, "Commit", header_format)
    commit_stat_sheet.write(0, 1, "Date", header_format)
    commit_stat_sheet.write(0, 2, "Code lines", header_format)
    commit_stat_sheet.write(0, 3, "Avg indent", header_format)
    commit_stat_sheet.write(0, 4, "Stddev indent", header_format)
    commit_stat_sheet.write(0, 5, "Max indent", header_format)
    commit_stat_sheet.write(0, 6, "Complexity", header_format)
    row = 1
    for commit_stats_item in commit_stats:
        row_str = str(row + 1)
        stats = commit_stats_item["stats"]
        commit = commit_stats_item["commit"]
        dt = commit_stats_item["date"]
        commit_stat_sheet.write(row, 0, commit)
        commit_stat_sheet.write(row, 1, dt)
        commit_stat_sheet.write(row, 2, stats["cnt"])
        commit_stat_sheet.write(row, 3, stats["avg"], indent_format)
        commit_stat_sheet.write(row, 4, stats["stddev"], indent_format)
        commit_stat_sheet.write(row, 5, stats["max"], indent_format)
        commit_stat_sheet.write_formula(
            row, 6, '=F' + row_str + '+E' + row_str + '*10+D' + row_str + '*5',
            indent_format,
            value=stats["max"] + stats["stddev"] * 10 + stats["avg"] * 5)
        row += 1
    commit_stat_sheet.set_column(0, 0, width=50)
    commit_stat_sheet.set_column(1, 1, width=20)
    commit_stat_sheet.set_column(2, 6, width=12)

    chart = workbook.add_chart({"type": "line"})
    chart.add_series({"name": "Lines of code",
                      "values": "=C2:C" + str(row + 1)})
    chart.add_series({"name": "Complexity",
                      "values": "=G2:G" + str(row + 1),
                      "y2_axis": True})
    chart.set_x_axis({'reverse': True})
    chart.set_y2_axis({"name": "Lines of code"})
    chart.set_y_axis({"name": "Complexity"})
    commit_stat_sheet.insert_chart(
        'A5', chart,
        options={
            'x_offset': 0,
            'y_offset': 0,
            'x_scale': 2,
            'y_scale': 2})

    file_sheet = workbook.add_worksheet("files")
    file_sheet.write(0, 0, "File", header_format)
    file_sheet.write(0, 1, "Revisions", header_format)
    file_sheet.write(0, 2, "Lines code", header_format)
    file_sheet.write(0, 3, "Avg indent", header_format)
    file_sheet.write(0, 4, "Stddev indent", header_format)
    file_sheet.write(0, 5, "Max indent", header_format)
    file_sheet.write(0, 6, "Complexity", header_format)
    row = 1
    for file in sorted([(files[file]["name"], file) for file in file_stats]):
        file_data = file_stats[file[1]]
        print(file_data)
        if file_data["deleted"]:
            continue
        complexity_stats = file_data["complexity"][0]["stats"]
        file_sheet.write(row, 0, file_data["name"])
        file_sheet.write(row, 1, file_data["commits"])
        file_sheet.write(row, 2, complexity_stats["lines code"])
        file_sheet.write(row, 3, complexity_stats["stats"]["avg"],
                         indent_format)
        file_sheet.write(row, 4, complexity_stats["stats"]["stddev"],
                         indent_format)
        file_sheet.write(row, 5, complexity_stats["stats"]["max"],
                         indent_format)
        row_str = str(row + 1)
        file_sheet.write_formula(
            row, 6, '=F' + row_str + '+E' + row_str + '*10+D' + row_str + '*5',
            indent_format,
            value=(
                (complexity_stats["stats"]["max"]
                 if complexity_stats["stats"]["max"] else 0.0) +
                (complexity_stats["stats"]["stddev"]
                 if complexity_stats["stats"]["stddev"] else 0.0) * 10.0 +
                (complexity_stats["stats"]["avg"]
                 if complexity_stats["stats"]["avg"] else 0.0) * 5.0))
        # print(file_data)
        row += 1

    file_sheet.set_column(0, 0, width=50)
    file_sheet.set_column(1, 6, width=12)

    try:
        workbook.close()
    except PermissionError:
        print("PermissionError on writing the file {}. Already opened?".format(
            xlsx_file))

    print("Done")


load_settings()
repo = import_repo(path)
print("Repository imported")
# print_config(repo)
# print_branches(repo)
# # print_commits(repo, print_files=False)
files = collect_stats_per_file(repo)
# print_file_stats(files, print_deleted=False)

commit_stats = collect_stats_per_commit(repo)
# print_commit_stats(commit_stats)
create_xlsx_report(xlsx_report, commit_stats, files)
