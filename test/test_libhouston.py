#!/usr/bin/python3
''' Unit Tests for Houston Satellite / Spacewalk server control program

'''

import Houston.libhouston as libhouston
import unittest

spw = libhouston.Spacewalk()
pkg = libhouston.PKG(40472, spw)
pkg['version'] = '1.7.5rc2'
newer_versions = [
    '1.7.5rc2a',
    '2.0',
    '1.7.6',
    '1.8a',
    '1.7.5rc3',
]

older_versions = [
    '1.6',
    '1.7.a',
    '1.7.5',
    '0.0.0.1',
    '1.7.5rc1',
]

identical_versions = [
    '01.07.05rc0002',
    '1.7.5rc2',
    '01.7.5rc2',
    '1_7.5-rc2',
    '1.7.5rc2',
]

pkg_keys = [
    "id", "name", "epoch", "version", "release", "arch_label",
    "providing_channels", "build_host", "description", "checksum",
    "checksum_type", "vendor", "summary", "cookie", "license", "file",
    "build_date", "last_modified_date", "size", "path", "payload_size", "url",
    "conflicts", "obsoletes", "requires", "files", "channels", "errata",
]


class TestPKGDetailsGoodID(unittest.TestCase):
    '''checks all appropriate fields are filled in on the package'''

    def test_DictionaryHasKeys(self):
        for key in pkg_keys:
            self.assertTrue(key in pkg.keys())


class TestPKGcomparisonsGoodStringInputs(unittest.TestCase):
    '''Tests the rich comparison functions for PKG'''

    def test_gt(self):
        '''Tests that > operator corectly returns True with string input'''
        for v in older_versions:
            self.assertTrue(pkg > v)

    def test_ge(self):
        '''Tests that >= operator corectly returns True with string input'''
        for v in older_versions + identical_versions:
            self.assertTrue(pkg >= v)

    def test_eq(self):
        '''Tests that == operator corectly returns True with string input'''
        for v in identical_versions:
            self.assertTrue(pkg == v)

    def test_ne(self):
        '''Tests that != operator corectly returns True with string input'''
        for v in newer_versions + older_versions:
            self.assertTrue(pkg != v)

    def test_le(self):
        '''Tests that <= operator corectly returns True with string input'''
        for v in newer_versions + identical_versions:
            self.assertTrue(pkg <= v)

    def test_lt(self):
        '''Tests that < operator corectly returns True with string input'''
        for v in newer_versions:
            self.assertTrue(pkg < v)


class TestPKGcomparisonsBadStringInputs(unittest.TestCase):
    '''Tests the rich comparison functions for PKG'''

    def test_gt(self):
        '''Tests that > operator corectly returns False with string input'''
        for v in newer_versions + identical_versions:
            self.assertFalse(pkg > v)

    def test_ge(self):
        '''Tests that >= operator corectly returns False with string input'''
        for v in newer_versions:
            self.assertFalse(pkg >= v)

    def test_eq(self):
        '''Tests that == operator corectly returns False with string input'''
        for v in newer_versions + older_versions:
            self.assertFalse(pkg == v)

    def test_ne(self):
        '''Tests that != operator corectly returns False with string input'''
        for v in identical_versions:
            self.assertFalse(pkg != v)

    def test_le(self):
        '''Tests that <= operator corectly returns False with string input'''
        for v in older_versions:
            self.assertFalse(pkg <= v)

    def test_lt(self):
        '''Tests that < operator corectly returns False with string input'''
        for v in older_versions + identical_versions:
            self.assertFalse(pkg < v)


if __name__ == '__main__':
    unittest.main()
