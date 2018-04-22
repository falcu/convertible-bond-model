from models import default_tree as underTest
from tests.test_base import TestBase
import models.data as model_data


class TestDefaultTree(TestBase):

    def test_solve_chambersPaperRealExample(self):
        #lambda1, lambda2....
        expectedDefaultProbabilities = [0.00207207, 0.00537085, 0.00424289, 0.00817737, 0.00558215, 0.00703698]
        modelInput = model_data.chambersPaperRealExampleDefaultTreeInput(faceValue=1.0)
        defaultTree = underTest.DefaultTree(modelInput)

        defaultTree.solve()

        result = defaultTree.defaultProbabilities()
        self.assertAlmostEqualList(expectedDefaultProbabilities, result, delta=0.0001)

    def test_solve_chambersPaperRealExample_faceValue100(self):
        #lambda1, lambda2....
        expectedDefaultProbabilities = [0.00207207, 0.00537085, 0.00424289, 0.00817737, 0.00558215, 0.00703698]
        modelInput = model_data.chambersPaperRealExampleDefaultTreeInput(faceValue=100.0)
        defaultTree = underTest.DefaultTree(modelInput)

        defaultTree.solve()

        result = defaultTree.defaultProbabilities()
        self.assertAlmostEqualList(expectedDefaultProbabilities, result, delta=0.0001)

    def test_defaultProbabilityOfLevel_chambersPaperRealExample(self):
        expectedProbability = 0.00558215
        modelInput = model_data.chambersPaperRealExampleDefaultTreeInput(faceValue=100.0)
        defaultTree = underTest.DefaultTree(modelInput)

        defaultTree.solve()
        result = defaultTree.defaultProbabilityOfLevel(5)

        self.assertAlmostEqual(expectedProbability, result, delta=0.0001)

    def test_solve_chambersPaperSimpleExample(self):
        #lambda1, lambda2, lambda3
        expectedDefaultProbabilities = [0.0717214, 0.0774391, 0.0843733 ]
        modelInput = model_data.chambersPaperSimpleExampleDefaultTreeInput(faceValue=1.0)
        defaultTree = underTest.DefaultTree(modelInput)

        defaultTree.solve()

        result = defaultTree.defaultProbabilities()
        self.assertAlmostEqualList(expectedDefaultProbabilities, result, delta=0.0017)
