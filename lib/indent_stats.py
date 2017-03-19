'''
Functions related to the processing if the indentation statistincs
'''

from math import sqrt
from itertools import zip_longest


def process_indent_stats(indent_stats):
    '''Processes raw data about linde indentation of some code
    and returns the statistics about it.
    As an argument expects a list, like this: [4, 5, 10]
    That would mean that in the code there are 4 lines with zero indent,
    5 lines with one and 10 lines with two.
    The returned value is a dictionary looking like this:
    {
        "avg": <average indentation for the whole code>,
        "sum": <sum of the indentation (does not make too much sense)>,
        "cnt": <count of lines>,
        "max": <maximum indentation found in the input data>,
        "stddev": <standard deviation of the indentation>,
        "hist": <histogram, basically the same as the input argument>
    }
    '''
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
        "avg": avg, "sum": sum_, "cnt": cnt, "max": max_,
        "stddev": stddev, "hist": indent_stats}


def join_histogram(a, b):
    '''Joins two indentation histograms.
    Example: Joining of [1, 2, 3] and [2, 3] will return [3, 5, 3]
    '''
    return [
        (a if a is not None else 0) + (b if b is not None else 0)
        for (a, b) in zip_longest(a, b)]
