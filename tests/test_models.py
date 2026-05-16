"""
Unit tests for the Crypto/Stock Price Tracker application.
Tests core models and business logic.
"""

import unittest
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import patch

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from models import Asset, Portfolio
from validators import InputValidator, SymbolValidator
from services import PortfolioService, CurrencyConverter, PriceService


class TestAsset(unittest.TestCase):
    """Test cases for Asset class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.asset = Asset('BTC', 2.5, 50000)
    
    def test_asset_creation(self):
        """Test asset creation with valid data."""
        self.assertEqual(self.asset.symbol, 'BTC')
        self.assertEqual(self.asset.quantity, 2.5)
        self.assertEqual(self.asset.purchase_price, 50000)
    
    def test_asset_invalid_quantity(self):
        """Test asset creation with invalid quantity."""
        with self.assertRaises(ValueError):
            Asset('BTC', -1, 50000)
        
        with self.assertRaises(ValueError):
            Asset('BTC', 0, 50000)
    
    def test_asset_invalid_price(self):
        """Test asset creation with invalid price."""
        with self.assertRaises(ValueError):
            Asset('BTC', 1, -50000)
        
        with self.assertRaises(ValueError):
            Asset('BTC', 1, 0)
    
    def test_asset_profit_loss_calculation(self):
        """Test profit/loss calculation."""
        asset = Asset('BTC', 2, 50000, current_price=55000)
        pl = asset.calculate_profit_loss()
        
        self.assertEqual(pl['purchase_value'], 100000)
        self.assertEqual(pl['current_value'], 110000)
        self.assertEqual(pl['profit_loss'], 10000)
        self.assertEqual(pl['profit_loss_percent'], 10.0)
    
    def test_asset_loss_calculation(self):
        """Test loss calculation."""
        asset = Asset('ETH', 10, 3000, current_price=2700)
        pl = asset.calculate_profit_loss()
        
        self.assertEqual(pl['purchase_value'], 30000)
        self.assertEqual(pl['current_value'], 27000)
        self.assertEqual(pl['profit_loss'], -3000)
        self.assertEqual(pl['profit_loss_percent'], -10.0)
    
    def test_asset_to_dict(self):
        """Test asset serialization to dictionary."""
        asset = Asset('BTC', 1, 50000, '2024-01-01', 55000)
        asset_dict = asset.to_dict()
        
        self.assertEqual(asset_dict['symbol'], 'BTC')
        self.assertEqual(asset_dict['quantity'], 1)
        self.assertEqual(asset_dict['purchase_price'], 50000)
        self.assertEqual(asset_dict['current_price'], 55000)
    
    def test_asset_from_dict(self):
        """Test asset deserialization from dictionary."""
        data = {
            'symbol': 'BTC',
            'quantity': 1,
            'purchase_price': 50000,
            'purchase_date': '2024-01-01',
            'current_price': 55000
        }
        
        asset = Asset.from_dict(data)
        self.assertEqual(asset.symbol, 'BTC')
        self.assertEqual(asset.quantity, 1)


class TestPortfolio(unittest.TestCase):
    """Test cases for Portfolio class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.portfolio = Portfolio("Test Portfolio")
        self.asset1 = Asset('BTC', 1, 50000, current_price=55000)
        self.asset2 = Asset('ETH', 10, 3000, current_price=3300)
    
    def test_portfolio_creation(self):
        """Test portfolio creation."""
        self.assertEqual(self.portfolio.name, "Test Portfolio")
        self.assertEqual(len(self.portfolio), 0)
    
    def test_add_asset(self):
        """Test adding asset to portfolio."""
        self.portfolio.add_asset(self.asset1)
        self.assertEqual(len(self.portfolio), 1)
        self.assertIsNotNone(self.portfolio.get_asset('BTC'))
    
    def test_add_multiple_assets(self):
        """Test adding multiple assets."""
        self.portfolio.add_asset(self.asset1)
        self.portfolio.add_asset(self.asset2)
        
        self.assertEqual(len(self.portfolio), 2)
    
    def test_remove_asset(self):
        """Test removing asset."""
        self.portfolio.add_asset(self.asset1)
        result = self.portfolio.remove_asset('BTC')
        
        self.assertTrue(result)
        self.assertEqual(len(self.portfolio), 0)
    
    def test_remove_nonexistent_asset(self):
        """Test removing non-existent asset."""
        result = self.portfolio.remove_asset('NONEXISTENT')
        self.assertFalse(result)
    
    def test_get_total_value(self):
        """Test total portfolio value calculation."""
        self.portfolio.add_asset(self.asset1)
        self.portfolio.add_asset(self.asset2)
        
        # BTC: 1 * 55000 = 55000
        # ETH: 10 * 3300 = 33000
        # Total: 88000
        total = self.portfolio.get_total_value()
        self.assertEqual(total, 88000)
    
    def test_get_total_purchase_value(self):
        """Test total purchase value."""
        self.portfolio.add_asset(self.asset1)
        self.portfolio.add_asset(self.asset2)
        
        # BTC: 1 * 50000 = 50000
        # ETH: 10 * 3000 = 30000
        # Total: 80000
        total = self.portfolio.get_total_purchase_value()
        self.assertEqual(total, 80000)
    
    def test_get_total_profit_loss(self):
        """Test total profit/loss calculation."""
        self.portfolio.add_asset(self.asset1)
        self.portfolio.add_asset(self.asset2)
        
        summary = self.portfolio.get_total_profit_loss()
        
        self.assertEqual(summary['total_invested'], 80000)
        self.assertEqual(summary['total_value'], 88000)
        self.assertEqual(summary['total_profit_loss'], 8000)
        self.assertEqual(summary['total_profit_loss_percent'], 10.0)
    
    def test_search_assets(self):
        """Test asset search."""
        self.portfolio.add_asset(self.asset1)
        self.portfolio.add_asset(self.asset2)
        
        results = self.portfolio.search_assets('BTC')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].symbol, 'BTC')
    
    def test_portfolio_iteration(self):
        """Test portfolio iteration."""
        self.portfolio.add_asset(self.asset1)
        self.portfolio.add_asset(self.asset2)
        
        symbols = [asset.symbol for asset in self.portfolio]
        self.assertIn('BTC', symbols)
        self.assertIn('ETH', symbols)
    
    def test_portfolio_to_dict(self):
        """Test portfolio serialization."""
        self.portfolio.add_asset(self.asset1)
        portfolio_dict = self.portfolio.to_dict()
        
        self.assertEqual(portfolio_dict['name'], "Test Portfolio")
        self.assertEqual(len(portfolio_dict['assets']), 1)
    
    def test_portfolio_from_dict(self):
        """Test portfolio deserialization."""
        self.portfolio.add_asset(self.asset1)
        data = self.portfolio.to_dict()
        
        new_portfolio = Portfolio.from_dict(data)
        self.assertEqual(len(new_portfolio), 1)
        self.assertIsNotNone(new_portfolio.get_asset('BTC'))


class TestInputValidator(unittest.TestCase):
    """Test cases for InputValidator class."""
    
    def test_validate_symbol_valid(self):
        """Test valid symbol validation."""
        self.assertTrue(InputValidator.validate_symbol('BTC'))
        self.assertTrue(InputValidator.validate_symbol('AAPL'))
        self.assertTrue(InputValidator.validate_symbol('A'))
    
    def test_validate_symbol_invalid(self):
        """Test invalid symbol validation."""
        self.assertFalse(InputValidator.validate_symbol('btc'))  # lowercase
        self.assertFalse(InputValidator.validate_symbol('BTC123'))  # numbers
        self.assertFalse(InputValidator.validate_symbol(''))  # empty
        self.assertFalse(InputValidator.validate_symbol('BTC-USD'))  # dash
    
    def test_validate_price_valid(self):
        """Test valid price validation."""
        self.assertTrue(InputValidator.validate_price('100'))
        self.assertTrue(InputValidator.validate_price('100.50'))
        self.assertTrue(InputValidator.validate_price('0.001'))
    
    def test_validate_price_invalid(self):
        """Test invalid price validation."""
        self.assertFalse(InputValidator.validate_price('-100'))  # negative
        self.assertFalse(InputValidator.validate_price('0'))  # zero
        self.assertFalse(InputValidator.validate_price('abc'))  # text
    
    def test_validate_quantity_valid(self):
        """Test valid quantity validation."""
        self.assertTrue(InputValidator.validate_quantity('1'))
        self.assertTrue(InputValidator.validate_quantity('1.5'))
        self.assertTrue(InputValidator.validate_quantity('0.00001'))
    
    def test_validate_quantity_invalid(self):
        """Test invalid quantity validation."""
        self.assertFalse(InputValidator.validate_quantity('-1'))  # negative
        self.assertFalse(InputValidator.validate_quantity('0'))  # zero
        self.assertFalse(InputValidator.validate_quantity('abc'))  # text
    
    def test_validate_date_valid(self):
        """Test valid date validation."""
        self.assertTrue(InputValidator.validate_date('2024-01-15'))
        self.assertTrue(InputValidator.validate_date('2025-12-31'))
    
    def test_validate_date_invalid(self):
        """Test invalid date validation."""
        self.assertFalse(InputValidator.validate_date('01-15-2024'))  # wrong format
        self.assertFalse(InputValidator.validate_date('2024/01/15'))  # slashes
        self.assertFalse(InputValidator.validate_date('01/15/2024'))  # wrong format
    
    def test_sanitize_symbol(self):
        """Test symbol sanitization."""
        self.assertEqual(InputValidator.sanitize_symbol('btc'), 'BTC')
        self.assertEqual(InputValidator.sanitize_symbol('  BTC  '), 'BTC')
        self.assertEqual(InputValidator.sanitize_symbol('BTC-USD'), 'BTCUSD')
    
    def test_validate_input_batch(self):
        """Test batch input validation."""
        inputs = {
            'symbol': 'BTC',
            'price': '50000',
            'quantity': '1'
        }
        
        is_valid, errors = InputValidator.validate_input_batch(inputs)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_validate_input_batch_with_errors(self):
        """Test batch validation with errors."""
        inputs = {
            'symbol': 'btc',  # invalid
            'price': '-100',  # invalid
            'quantity': 'abc'  # invalid
        }
        
        is_valid, errors = InputValidator.validate_input_batch(inputs)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)


class TestSymbolValidator(unittest.TestCase):
    """Test cases for SymbolValidator class."""
    
    def test_is_known_crypto(self):
        """Test crypto symbol recognition."""
        self.assertTrue(SymbolValidator.is_known_crypto('BTC'))
        self.assertTrue(SymbolValidator.is_known_crypto('ETH'))
        self.assertFalse(SymbolValidator.is_known_crypto('UNKNOWN'))
    
    def test_is_known_stock(self):
        """Test stock symbol recognition."""
        self.assertTrue(SymbolValidator.is_known_stock('AAPL'))
        self.assertTrue(SymbolValidator.is_known_stock('MSFT'))
        self.assertFalse(SymbolValidator.is_known_stock('UNKNOWN'))
    
    def test_get_suggestions(self):
        """Test symbol suggestions."""
        suggestions = SymbolValidator.get_suggestions('BT')
        self.assertIn('BTC', suggestions)


class TestCurrencyConverter(unittest.TestCase):
    """Test cases for CurrencyConverter class."""
    
    def test_convert_same_currency(self):
        """Test converting same currency."""
        result = CurrencyConverter.convert(100, 'USD', 'USD')
        self.assertEqual(result, 100)
    
    def test_convert_different_currencies(self):
        """Test converting different currencies."""
        result = CurrencyConverter.convert(100, 'USD', 'EUR')
        self.assertIsNotNone(result)
        self.assertLess(result, 100)  # EUR is worth more than USD
    
    def test_convert_invalid_currency(self):
        """Test converting invalid currency."""
        result = CurrencyConverter.convert(100, 'INVALID', 'USD')
        self.assertIsNone(result)
    
    def test_get_supported_currencies(self):
        """Test getting supported currencies."""
        currencies = CurrencyConverter.get_supported_currencies()
        self.assertIn('USD', currencies)
        self.assertIn('EUR', currencies)


class TestPriceService(unittest.TestCase):
    """Test cases for crypto price service helpers."""

    @patch('services.PriceService.fetch_multiple_prices')
    def test_fetch_prices_in_usdt_converts_usd_prices(self, mock_fetch):
        """Test converting fetched USD prices into USDT prices."""
        mock_fetch.return_value = {
            'BTC': 50000.0,
            'ETH': 3000.0,
            'USDT': 0.999
        }

        prices = PriceService.fetch_prices_in_usdt(['btc', 'ETH', 'USDT'])

        self.assertAlmostEqual(prices['BTC'], 50000.0 / 0.999)
        self.assertAlmostEqual(prices['ETH'], 3000.0 / 0.999)
        self.assertEqual(prices['USDT'], 1.0)

    @patch('services.PriceService.fetch_multiple_prices')
    def test_fetch_prices_in_usdt_keeps_unavailable_prices(self, mock_fetch):
        """Test unavailable prices remain visible as missing data."""
        mock_fetch.return_value = {
            'BTC': None,
            'USDT': 1.0
        }

        prices = PriceService.fetch_prices_in_usdt(['BTC'])

        self.assertIsNone(prices['BTC'])


def run_tests():
    """Run all unit tests."""
    unittest.main(verbosity=2)


if __name__ == '__main__':
    run_tests()
