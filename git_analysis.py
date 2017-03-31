#!/usr/bin/python3


from git import Repo
from git.exc import InvalidGitRepositoryError

import datetime
from itertools import cycle
import sys
import yaml
from lib.indent_stats import *
from lib.file_names import *
import dateutil.parser


path = ''
ignored_files = []
xlsx_report = ''
ignore_one_char_lines = True
since = None
commit_count = 0
show_deleted_files = False

spinner = cycle(['-', '\\', '|', '/'])


def print_spinner(commit_no):
    global commit_count
    sys.stdout.write("\b\b\b\b\b\b{:>3}% {}".format(
        round(commit_no / commit_count * 100), next(spinner)))
    sys.stdout.flush()


def load_settings():
    settings_file = 'git_analysis.yml'
    global path
    global ignored_files
    global xlsx_report
    global since
    global show_deleted_files
    with open(settings_file) as yml_file:
        try:
            file_data = yaml.load(yml_file)
            path = file_data["path"]
            ignored_files = file_data["ignored_files"]
            xlsx_report = file_data["report"]
            if "since" in file_data:
                since = dateutil.parser.parse(file_data["since"])
            if "show_deleted_files" in file_data:
                show_deleted_files = file_data["show_deleted_files"]
        except yaml.YAMLError as e:
            print("Cannot parse the settings file {}: {}".format(
                settings_file, str(e)))
            exit(1)
        except KeyError as e:
            print("Cannot find a required config parameter", str(e))


def import_repo(path):
    global commit_count
    try:
        repo = Repo(path)
        for commit in repo.iter_commits():
            if since:
                if datetime.datetime.fromtimestamp(
                        commit.committed_date) < since:
                    continue
            commit_count += 1
        print("Repository imported, the number of commits is {}".format(
            commit_count))
        return repo
    except InvalidGitRepositoryError as e:
        print("Invalid git repository {}".format(str(e)))
        exit(1)


def collect_stats_per_file(repo):
    print("Collecting file statistics...")
    files = {}
    commit_no = 1
    for commit in repo.iter_commits():
        if since:
            if datetime.datetime.fromtimestamp(commit.committed_date) < since:
                continue
        print_spinner(commit_no)
        commit_no += 1
        sys.stdout.flush()
        tree_info = collect_complexity_stats_from_file_tree(commit.tree)
        file_stats = commit.stats.files
        for file in file_stats:
            old_name, new_name = process_renamed_file(file)
            if (ignore_file(old_name, ignored_files) or
                    ignore_file(new_name, ignored_files)):
                continue
            stats = file_stats[file]
            if new_name not in files:
                files[old_name] = {
                    "commits": 0, "lines": 0, "insertions": 0, "deletions": 0,
                    "deleted": False, "name": new_name, "complexity": []}
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
            file_complexity_stats = get_stats_for_file(tree_info, new_name)
            if file_complexity_stats:
                files[old_name]["complexity"].append({
                    "commit": str(commit),
                    "stats": file_complexity_stats})
            else:
                files[old_name]["deleted"] = True
    print("\bDone")
    return files


def remove_python_docstring(lines):
    result = []
    wait_for_docstring = True
    in_docstring = False
    for line in lines:
        linestrip = line.strip()
        if wait_for_docstring and line.startswith('#!'):
            continue
        if wait_for_docstring and (
                linestrip.startswith("'''") or linestrip.startswith('"""')):
            in_docstring = True
            wait_for_docstring = False
            if linestrip == "'''" or linestrip == '"""':
                continue
        if in_docstring and (
                linestrip.endswith("'''") or linestrip.endswith('"""')):
            in_docstring = False
            continue
        if in_docstring:
            continue
        result.append(line)
        if (linestrip.startswith('def ') or linestrip.startswith("class ")):
            wait_for_docstring = True
    return result


def analyze_complexity(blob):
    lines = blob.data_stream.read().decode().split('\n')
    lines_filtered = [
        l for l in lines
        if len(l.strip()) > (1 if ignore_one_char_lines else 0)]
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
            if ignore_file(item.path, ignored_files):
                continue
            try:
                result.append({
                    "path": item.path, "size": item.size,
                    "mime_type": item.mime_type,
                    "complexity": analyze_complexity(item)})
            except UnicodeDecodeError as e:
                print("Failed to decode file {}. Skipping...".format(
                    item.path))
        elif type(item).__name__ == 'Tree':
            result = result + collect_complexity_stats_from_file_tree(item)
        else:
            print("Dont know how to work with type", type(item).__name__)
    return result


def get_stats_for_file(tree_info, file):
    for tree_item in tree_info:
        if tree_item["path"] == file:
            return tree_item["complexity"]


def collect_stats_per_commit(repo):
    print("Collecting complexity statistics for each revision...")
    result = []
    commit_no = 1
    for commit in repo.iter_commits():
        if since:
            if datetime.datetime.fromtimestamp(commit.committed_date) < since:
                continue
        print_spinner(commit_no)
        commit_no += 1
        sys.stdout.flush()
        tree_info = collect_complexity_stats_from_file_tree(commit.tree)
        indent_hist = []
        for tree_item in tree_info:
            # print(tree_item)
            indent_hist = join_histogram(
                indent_hist, tree_item["complexity"]["stats"]["hist"])
        stats = process_indent_stats(indent_hist)
        result.append({
            "commit": str(commit), "stats": stats,
            "date": datetime.datetime.fromtimestamp(
                commit.committed_date).strftime('%Y-%m-%d %H:%M:%S')})
    print("\bDone")
    return result


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
            value=(
                (stats["max"] if stats["max"] else 0.0) +
                (stats["stddev"] if stats["stddev"] else 0.0) * 10 +
                (stats["avg"] if stats["avg"] else 0.0) * 5))
        row += 1
    commit_stat_sheet.set_column(0, 0, width=50)
    commit_stat_sheet.set_column(1, 1, width=20)
    commit_stat_sheet.set_column(2, 6, width=12)

    chart = workbook.add_chart({"type": "line"})
    chart.add_series({"name": "Lines of code", "values": "=C2:C" + row_str})
    chart.add_series(
        {"name": "Complexity", "values": "=G2:G" + row_str, "y2_axis": True})
    chart.set_x_axis({'reverse': True})
    chart.set_y2_axis({"name": "Lines of code"})
    chart.set_y_axis({"name": "Complexity"})
    commit_stat_sheet.insert_chart(
        'A5', chart,
        options={'x_offset': 0, 'y_offset': 0, 'x_scale': 2, 'y_scale': 2})

    file_sheet = workbook.add_worksheet("files")
    file_sheet.write(0, 0, "File", header_format)
    file_sheet.write(0, 1, "Revisions", header_format)
    file_sheet.write(0, 2, "Lines code last 5 revisions", header_format)
    file_sheet.write(0, 7, "Complexity in last 5 revisions", header_format)
    file_sheet.write(0, 12, "Avg indent", header_format)
    file_sheet.write(0, 13, "Stddev indent", header_format)
    file_sheet.write(0, 14, "Max indent", header_format)
    global show_deleted_files
    if show_deleted_files:
        file_sheet.write(0, 15, "Deleted", header_format)
    row = 1
    for file in sorted([(files[file]["name"], file) for file in file_stats]):
        file_data = file_stats[file[1]]
        if file_data["deleted"] and not show_deleted_files:
            continue
        file_sheet.write(row, 0, file_data["name"])
        file_sheet.write(row, 1, file_data["commits"])
        if show_deleted_files and file_data["deleted"]:
            file_sheet.write(row, 14, True)
        if len(file_data["complexity"]):
            complexity_stats = file_data["complexity"][0]["stats"]
            file_sheet.write(
                row, 12, complexity_stats["stats"]["avg"], indent_format)
            file_sheet.write(
                row, 13, complexity_stats["stats"]["stddev"], indent_format)
            file_sheet.write(
                row, 14, complexity_stats["stats"]["max"], indent_format)
            for revision in range(0, 5):
                if len(file_data["complexity"]) <= revision:
                    break
                complexity_stats = file_data["complexity"][revision]["stats"]
                file_sheet.write(row, 7 + revision, round(
                    (complexity_stats["stats"]["max"]
                     if complexity_stats["stats"]["max"] else 0.0) +
                    (complexity_stats["stats"]["stddev"]
                     if complexity_stats["stats"]["stddev"] else 0.0) * 10.0 +
                    (complexity_stats["stats"]["avg"]
                     if complexity_stats["stats"]["avg"] else 0.0) * 5.0, 3))
                file_sheet.write(
                    row, 2 + revision, complexity_stats["lines code"])
        # print(file_data)
        row += 1

    file_sheet.set_column(0, 0, width=50)
    file_sheet.set_column(1, 16, width=10)

    try:
        workbook.close()
    except PermissionError:
        print("PermissionError on writing the file {}. Already opened?".format(
            xlsx_file))

    print("Done")


load_settings()
repo = import_repo(path)
files = collect_stats_per_file(repo)
commit_stats = collect_stats_per_commit(repo)

create_xlsx_report(xlsx_report, commit_stats, files)
