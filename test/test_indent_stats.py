'''
Unit tests for git_analysis.py
'''

import unittest


class ProcessIndentStats(unittest.TestCase):

    def setUp(self):
        from lib.indent_stats import process_indent_stats
        self.process_indent_stats = process_indent_stats

    def test_FunctionExists(self):
        '''Can import the function process_indent_stats'''
        self.assertIsNotNone(self.process_indent_stats)

    def test_ProcessEmpty(self):
        '''Returns something on empty histogram'''
        histogram = []
        result = self.process_indent_stats(histogram)
        expected_result = {
            "cnt": 0,
            "sum": 0,
            "max": 0,
            "stddev": None,
            "avg": None,
            "hist": []}
        self.assertEqual(result, expected_result)

    def test_ProcessZeroes(self):
        '''Returns something on sero histogram'''
        histogram = [0]
        result = self.process_indent_stats(histogram)
        expected_result = {
            "cnt": 0,
            "sum": 0,
            "max": 1,
            "stddev": None,
            "avg": None,
            "hist": [0]}
        self.assertEqual(result, expected_result)

    def test_ProcessOne(self):
        '''Returns something on sero histogram'''
        histogram = [1]
        result = self.process_indent_stats(histogram)
        expected_result = {
            "cnt": 1,
            "sum": 1,
            "max": 1,
            "stddev": 0,
            "avg": 1,
            "hist": [1]}
        self.assertEqual(result, expected_result)

    def test_ProcessOneTwoThree(self):
        '''Returns something on sero histogram'''
        histogram = [1, 2, 3]
        result = self.process_indent_stats(histogram)
        expected_result = {
            "cnt": 6,
            "sum": 14,
            "max": 3,
            "stddev": 0.745,
            "avg": 2.333,
            "hist": [1, 2, 3]}
        result["avg"] = round(result["avg"], 3)
        result["stddev"] = round(result["stddev"], 3)
        self.assertEqual(result, expected_result)


class JoinHistogram(unittest.TestCase):

    def setUp(self):
        from lib.indent_stats import join_histogram
        self.join_histogram = join_histogram

    def test_FunctionExists(self):
        self.assertIsNotNone(self.join_histogram)

    def test_BothEmpty(self):
        '''Returns empty on emtpy input'''
        a = []
        b = []
        result = self.join_histogram(a, b)
        expected_result = []
        self.assertEqual(result, expected_result)

    def test_AEmpty(self):
        '''Returns empty on emtpy input'''
        a = []
        b = [1]
        result = self.join_histogram(a, b)
        expected_result = [1]
        self.assertEqual(result, expected_result)

    def test_BEmpty(self):
        '''Returns empty on emtpy input'''
        a = [1]
        b = []
        result = self.join_histogram(a, b)
        expected_result = [1]
        self.assertEqual(result, expected_result)

    def test_123(self):
        '''Returns empty on emtpy input'''
        a = [1, 2, 3]
        b = [1, 2, 3]
        result = self.join_histogram(a, b)
        expected_result = [2, 4, 6]
        self.assertEqual(result, expected_result)

    def test_diff_len(self):
        '''Returns empty on emtpy input'''
        a = [1, 2, 3]
        b = [1, 2]
        result = self.join_histogram(a, b)
        expected_result = [2, 4, 3]
        self.assertEqual(result, expected_result)
