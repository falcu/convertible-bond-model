from models import stock_tree as underTest
from tests.test_base import TestBase


class TestStockTree(TestBase):
    def test_solve_chambersPaper_stockTreeIsBuiltCorrectly(self):
        expectedStockPrices = [15.006, 10.5341, 21.3764, 7.3948, 15.006, 30.4511, 5.1911, 10.5341, 21.3764, 43.3782,
                               3.6441, 7.3948, 15.006, 30.4511, 61.7932, 2.5581, 5.1911, 10.5341, 21.3764, 43.3782,
                               88.0258, 1.7958, 3.6441, 7.3948, 15.006, 30.4511, 61.7932, 125.3947]
        stockTree = underTest.StockTree(7, 15.006, 0.353836, 1)

        stockTree.solve()
        actualStockPrices = stockTree.stockPricesByLevel()
        self.assertAlmostEqualList( expectedStockPrices, actualStockPrices)

    def test_stockPricesOfLevel_chambersPaper_stockTreeIsBuiltCorrectly(self):
        expectedStockPrices = [1.7958, 3.6441, 7.3948, 15.006, 30.4511, 61.7932, 125.3947]
        stockTree = underTest.StockTree(7, 15.006, 0.353836, 1)

        stockTree.solve()
        actualStockPrices = stockTree.stockPricesOfLevel(7)

        self.assertAlmostEqualList( expectedStockPrices, actualStockPrices)
