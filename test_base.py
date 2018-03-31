import unittest

class TestBase(unittest.TestCase):

    def assertAlmostEqualList(self, expectedList, actualList, delta=0.0001 ):
        self.assertEqual(len(expectedList), len(actualList))
        for i in range(0,len(expectedList)):
            self.assertAlmostEqual(expectedList[i], actualList[i], delta=delta)