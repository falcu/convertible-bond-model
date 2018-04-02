from models import default_tree as underTest
from tests.test_base import TestBase


class TestDefaultTree(TestBase):

    def test_solve_chambersPaperRealExample(self):
        #lambda1, lambda2....
        expectedDefaultProbabilities = [0.00207207, 0.00537085, 0.00424289, 0.00817737, 0.00558215, 0.00703698]
        zeroCouponRates = [0.05969, 0.06209, 0.06373, 0.06455, 0.06504, 0.06554]
        volatility = 0.1
        deltaTime = 1.0
        faceValue = 1.0
        riskyZeroCoupons = [0.0611, 0.0646, 0.0663, 0.0678, 0.0683, 0.06894]
        recovery = 0.32
        defaultTree = underTest.DefaultTree(zeroCouponRates, volatility, deltaTime, faceValue, riskyZeroCoupons, recovery)

        defaultTree.solve()

        result = defaultTree.defaultProbabilities()
        self.assertAlmostEqualList(expectedDefaultProbabilities, result, delta=0.0001)

    def test_solve_chambersPaperSimpleExample(self):
        #lambda1, lambda2, lambda3
        expectedDefaultProbabilities = [0.0717214, 0.0774391, 0.0843733 ]
        #R0, R1, R2
        zeroCouponRates = [0.1, 0.1, 0.1]
        volatility = 0.1
        deltaTime = 1.0
        faceValue = 1.0
        riskyZeroCoupons = [0.15,0.15,0.15]
        recovery = 0.32
        defaultTree = underTest.DefaultTree(zeroCouponRates, volatility, deltaTime, faceValue, riskyZeroCoupons, recovery)

        defaultTree.solve()

        result = defaultTree.defaultProbabilities()
        self.assertAlmostEqualList(expectedDefaultProbabilities, result, delta=0.0017)
