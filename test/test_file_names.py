#!/usr/bin/python3


import unittest


class IgnoreFile(unittest.TestCase):

    def setUp(self):
        from lib.file_names import ignore_file
        self.ignore_file = ignore_file

    def test_FunctionExists(self):
        '''Can import the function ignore_file'''
        self.assertIsNotNone(self.ignore_file)

    def test_returns_True_on_ignored(self):
        '''Returns True when the file is in the list'''
        lst = ['a', 'b', 'c']
        file = 'b'
        result = self.ignore_file(file, lst)
        expected_result = True
        self.assertEqual(result, expected_result)

    def test_returns_True_on_pattern_match(self):
        '''Returns True when the file matches a pattern'''
        lst = ['a', 'b', 'c']
        file = 'bobba'
        result = self.ignore_file(file, lst)
        expected_result = True
        self.assertEqual(result, expected_result)

    def test_returns_None_on_no_pattern_match(self):
        '''Returns True when the file matches a pattern'''
        lst = ['a', 'b', 'c']
        file = 'zzzz'
        result = self.ignore_file(file, lst)
        expected_result = None
        self.assertEqual(result, expected_result)

    def test_returns_None_on_no_file_name(self):
        '''Returns True when the file matches a pattern'''
        lst = ['a', 'b', 'c']
        file = None
        result = self.ignore_file(file, lst)
        expected_result = None
        self.assertEqual(result, expected_result)


class ProcessRenamedFile(unittest.TestCase):

    def setUp(self):
        from lib.file_names import process_renamed_file
        self.process_renamed_file = process_renamed_file

    def test_FunctionExists(self):
        '''Can import the function process_renamed_file'''
        self.assertIsNotNone(self.process_renamed_file)

    def test_no_rename(self):
        '''Returns the same as input when no rename is happening'''
        file = 'abc.def'
        result = self.process_renamed_file(file)
        expected_result = (file, file)
        self.assertEqual(result, expected_result)

    def test_no_rename_path(self):
        '''Returns the same as input when no rename is happening'''
        file = 'tests/abc.def'
        result = self.process_renamed_file(file)
        expected_result = (file, file)
        self.assertEqual(result, expected_result)

    def test_simple_rename(self):
        '''Returns the same as input when no rename is happening'''
        file = 'a => b'
        result = self.process_renamed_file(file)
        expected_result = ('a', 'b')
        self.assertEqual(result, expected_result)

    def test_rename_path(self):
        '''Returns the same as input when no rename is happening'''
        file = 'test/{a => b}/z'
        result = self.process_renamed_file(file)
        expected_result = ('test/a/z', 'test/b/z')
        self.assertEqual(result, expected_result)
