from models import risk_free_tree as underTest
from tests.test_base import TestBase
import models.data as model_data

class TestRiskFreeTree( TestBase ):

    def test_solve_chambersPaperRealExample(self):
        #R0, Rd, Ru, Rdd, Rud, Ruu, Rddd, Rudd, Ruud, Ruuu....
        expectedRates = [0.05969, 0.05808, 0.0709403, 0.0543898, 0.0664319, 0.08114, 0.049051, 0.0599109, 0.0731752,
                         0.0893761, 0.04426, 0.0540592, 0.0660279, 0.0806464, 0.0985016, 0.04059, 0.0495766, 0.0605529,
                         0.0739593, 0.0903339, 0.110334]
        modelInput = model_data.chambersPaperRealExampleRiskFreeInput( faceValue=1.0 )
        riskFreeTree = underTest.RiskFreeTree(modelInput)

        riskFreeTree.solve()

        result = riskFreeTree.ratesByLevel()
        self.assertAlmostEqualList(expectedRates, result, delta=0.00001)

    def test_solve_chambersPaperRealExample_faceValue100(self):
        #R0, Rd, Ru, Rdd, Rud, Ruu, Rddd, Rudd, Ruud, Ruuu....
        expectedRates = [0.05969, 0.05808, 0.0709403, 0.0543898, 0.0664319, 0.08114, 0.049051, 0.0599109, 0.0731752,
                         0.0893761, 0.04426, 0.0540592, 0.0660279, 0.0806464, 0.0985016, 0.04059, 0.0495766, 0.0605529,
                         0.0739593, 0.0903339, 0.110334]
        #R0, R1, R2, R3, R4, R5
        modelInput = model_data.chambersPaperRealExampleRiskFreeInput()
        riskFreeTree = underTest.RiskFreeTree(modelInput)

        riskFreeTree.solve()

        result = riskFreeTree.ratesByLevel()
        self.assertAlmostEqualList(expectedRates, result, delta=0.00001)

    def test_ratesOfLevel_chambersPaperRealExample(self):
        #Rddddd, Rudddd...
        expectedRates = [ 0.04059, 0.0495766, 0.0605529, 0.0739593, 0.0903339, 0.110334]
        modelInput = model_data.chambersPaperRealExampleRiskFreeInput()
        riskFreeTree = underTest.RiskFreeTree(modelInput)

        riskFreeTree.solve()
        result = riskFreeTree.ratesOfLevel(6)

        self.assertAlmostEqualList(expectedRates, result, delta=0.00001)

    def test_solve_chambersPaperSimpleExample(self):
        #R0, Rd, Ru, Rdd, Rud, Ruu
        expectedRates = [0.1, 0.09000, 0.10990, 0.0813, 0.09930, 0.1213 ]
        modelInput = model_data.chambersPaperSimpleExampleRiskFreeInput(faceValue=1.0)
        riskFreeTree = underTest.RiskFreeTree(modelInput)

        riskFreeTree.solve()

        result = riskFreeTree.ratesByLevel()
        self.assertAlmostEqualList(expectedRates, result, delta=0.001)

