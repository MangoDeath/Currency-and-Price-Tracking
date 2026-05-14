import tempfile
import unittest
from pathlib import Path

from main import Asset, Portfolio


class AssetCalculationTests(unittest.TestCase):
    def test_profit_loss_calculations(self) -> None:
        asset = Asset(
            symbol="bitcoin",
            name="Bitcoin",
            asset_type="crypto",
            quantity=0.5,
            purchase_price=40_000,
            current_price=50_000,
        )

        self.assertEqual(asset.cost_basis, 20_000)
        self.assertEqual(asset.market_value, 25_000)
        self.assertEqual(asset.profit_loss, 5_000)
        self.assertEqual(asset.profit_loss_percent, 25)


class PortfolioPersistenceTests(unittest.TestCase):
    def test_save_load_and_remove_asset(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "portfolio.json"
            portfolio = Portfolio(path)
            asset = Asset(
                symbol="AAPL",
                name="Apple",
                asset_type="stock",
                quantity=2,
                purchase_price=150,
                current_price=175,
            )

            portfolio.add(asset)
            loaded = Portfolio(path)

            self.assertEqual(len(loaded.assets), 1)
            self.assertEqual(loaded.total_cost(), 300)
            self.assertEqual(loaded.total_value(), 350)
            self.assertEqual(loaded.total_profit_loss(), 50)

            loaded.remove([asset.id])
            self.assertEqual(Portfolio(path).assets, [])


if __name__ == "__main__":
    unittest.main()
