''' Unit Tests for Houston Satellite / Spacewalk server control program

'''

import libhouston
import unittest

spw = libhouston.Spacewalk()
pkg = libhouston.PKG(23, spw)
pkg['version'] = '1.7.5rc1'
bigger_versions = [
    '1.7.5rc1a',
    '2.0',
    '1.7.6',
    '1.8a',
]

smaller_versions = [
    '1.6',
    '1.7.a',
    '1.7.5',
    '0.0.0.1',
]

identical_versions = [
    '01.07.05rc0001',
    '1.7.5rc1',
    '01.7.5rc1',
    '1_7.5-rc1',
]


class TestPKGcomparisonsGoodInputs(unittest.TestCase):
    '''Tests the rich comparison functions for PKG'''

    def test_gt(self):
        '''Tests that > operator corectly returns True with string input'''
        for v in bigger_versions:
            self.assertTrue(pkg > v)

    def test_ge(self):
        '''Tests that >= operator corectly returns True with string input'''
        for v in bigger_versions + identical_versions:
            self.assertTrue(pkg >= v)

    def test_eq(self):
        '''Tests that == operator corectly returns True with string input'''
        for v in identical_versions:
            self.assertTrue(pkg == v)

    def test_ne(self):
        '''Tests that != operator corectly returns True with string input'''
        for v in smaller_versions + bigger_versions:
            self.assertTrue(pkg != v)

    def test_le(self):
        '''Tests that <= operator corectly returns True with string input'''
        for v in smaller_versions + identical_versions:
            self.assertTrue(pkg <= v)

    def test_lt(self):
        '''Tests that < operator corectly returns True with string input'''
        for v in smaller_versions:
            self.assertTrue(pkg < v)


class TestPKGcomparisonsBadInputs(unittest.TestCase):
    '''Tests the rich comparison functions for PKG'''

    def test_gt(self):
        '''Tests that > operator corectly returns False with string input'''
        for v in smaller_versions + identical_versions:
            self.assertFalse(pkg > v)

    def test_ge(self):
        '''Tests that >= operator corectly returns False with string input'''
        for v in smaller_versions:
            self.assertFalse(pkg >= v)

    def test_eq(self):
        '''Tests that == operator corectly returns False with string input'''
        for v in smaller_versions + bigger_versions:
            self.assertFalse(pkg == v)

    def test_ne(self):
        '''Tests that != operator corectly returns False with string input'''
        for v in identical_versions:
            self.assertFalse(pkg != v)

    def test_le(self):
        '''Tests that <= operator corectly returns False with string input'''
        for v in smaller_versions:
            self.assertFalse(pkg <= v)

    def test_lt(self):
        '''Tests that < operator corectly returns False with string input'''
        for v in smaller_versions + identical_versions:
            self.assertFalse(pkg < v)


if __name__ == '__main__':
    unittest.main()
