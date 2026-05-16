"""
Services module for API calls and business logic.
Handles real-time price fetching and portfolio management operations.
"""

import requests
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from models import Asset, Portfolio
from decorators import cache_result, retry, error_handler


class PriceService:
    """Fetches real-time price data from external APIs."""
    
    # CoinGecko API - Free, no authentication required
    COINGECKO_API = "https://api.coingecko.com/api/v3"
    
    # Crypto symbol mappings
    CRYPTO_IDS = {
        'BTC': 'bitcoin',
        'ETH': 'ethereum',
        'BNB': 'binancecoin',
        'XRP': 'ripple',
        'ADA': 'cardano',
        'SOL': 'solana',
        'DOT': 'polkadot',
        'DOGE': 'dogecoin',
        'SHIB': 'shiba-inu',
        'LINK': 'chainlink',
        'MATIC': 'matic-network',
        'AVAX': 'avalanche-2',
        'LTC': 'litecoin',
        'BCH': 'bitcoin-cash',
        'XMR': 'monero',
        'ATOM': 'cosmos',
        'ALGO': 'algorand',
        'USDT': 'tether',
        'USDC': 'usd-coin',
        'DAI': 'dai'
    }
    
    def __init__(self, currency: str = 'usd'):
        """Initialize price service with target currency."""
        self.currency = currency.lower()
        self.cache = {}
        self.cache_time = {}
    
    @staticmethod
    @retry(max_attempts=3, delay_seconds=1.0)
    def fetch_crypto_price(symbol: str, currency: str = 'usd') -> Optional[float]:
        """
        Fetch current price of cryptocurrency.
        Uses CoinGecko API which is free and doesn't require authentication.
        """
        crypto_id = PriceService.CRYPTO_IDS.get(symbol.upper())
        
        if not crypto_id:
            print(f"Warning: Unknown cryptocurrency symbol: {symbol}")
            return None
        
        try:
            url = f"{PriceService.COINGECKO_API}/simple/price"
            params = {
                'ids': crypto_id,
                'vs_currencies': currency.lower(),
                'include_market_cap': 'true',
                'include_24hr_vol': 'true'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if crypto_id in data and currency.lower() in data[crypto_id]:
                price = data[crypto_id][currency.lower()]
                print(f"[API] Fetched {symbol}: ${price:.2f}")
                return float(price)
            
            print(f"Warning: No price data for {symbol}")
            return None
        
        except requests.RequestException as e:
            print(f"Error fetching price for {symbol}: {e}")
            return None
    
    @staticmethod
    def fetch_multiple_prices(symbols: List[str], currency: str = 'usd') -> Dict[str, Optional[float]]:
        """
        Fetch prices for multiple cryptocurrencies at once.
        More efficient than calling fetch_crypto_price individually.
        """
        prices = {}
        
        # Filter to only known symbols
        crypto_ids = {sym: PriceService.CRYPTO_IDS[sym] 
                      for sym in symbols if sym in PriceService.CRYPTO_IDS}
        
        if not crypto_ids:
            return prices
        
        try:
            url = f"{PriceService.COINGECKO_API}/simple/price"
            params = {
                'ids': ','.join(crypto_ids.values()),
                'vs_currencies': currency.lower()
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            for symbol, crypto_id in crypto_ids.items():
                if crypto_id in data and currency.lower() in data[crypto_id]:
                    prices[symbol] = float(data[crypto_id][currency.lower()])
                else:
                    prices[symbol] = None
            
            print(f"[API] Fetched prices for {len(prices)} assets")
            return prices
        
        except requests.RequestException as e:
            print(f"Error fetching prices: {e}")
            return {sym: None for sym in crypto_ids.keys()}

    @staticmethod
    def fetch_prices_in_usdt(symbols: List[str]) -> Dict[str, Optional[float]]:
        """
        Fetch cryptocurrency prices expressed in USDT.
        CoinGecko returns fiat quote currencies, so this converts USD prices
        through the current USDT/USD price.
        """
        normalized_symbols = sorted({symbol.upper() for symbol in symbols})
        if not normalized_symbols:
            return {}

        quote_symbols = sorted(set(normalized_symbols) | {'USDT'})
        usd_prices = PriceService.fetch_multiple_prices(quote_symbols, 'usd')
        usdt_usd_price = usd_prices.get('USDT') or 1.0

        prices = {}
        for symbol in normalized_symbols:
            usd_price = usd_prices.get(symbol)
            if usd_price is None:
                prices[symbol] = None
            elif symbol == 'USDT':
                prices[symbol] = 1.0
            else:
                prices[symbol] = usd_price / usdt_usd_price

        return prices
    
    @staticmethod
    def get_supported_cryptos() -> Dict[str, str]:
        """Get list of supported cryptocurrencies."""
        return PriceService.CRYPTO_IDS.copy()
    
    @staticmethod
    def get_price_history(symbol: str, days: int = 30, currency: str = 'usd') -> Optional[List[Tuple[int, float]]]:
        """
        Fetch historical price data for a cryptocurrency.
        Returns list of (timestamp, price) tuples.
        """
        crypto_id = PriceService.CRYPTO_IDS.get(symbol.upper())
        
        if not crypto_id:
            return None
        
        try:
            url = f"{PriceService.COINGECKO_API}/coins/{crypto_id}/market_chart"
            params = {
                'vs_currency': currency.lower(),
                'days': min(days, 365),
                'interval': 'daily'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            prices = data.get('prices', [])
            
            print(f"[API] Fetched {len(prices)} historical prices for {symbol}")
            return prices
        
        except requests.RequestException as e:
            print(f"Error fetching price history: {e}")
            return None


class PortfolioService:
    """High-level portfolio management operations."""
    
    def __init__(self, portfolio: Portfolio, currency: str = 'usd'):
        """Initialize portfolio service."""
        self.portfolio = portfolio
        self.currency = currency
        self.price_service = PriceService(currency)
    
    def update_all_prices(self) -> bool:
        """
        Update current prices for all assets in portfolio.
        Fetches from API and updates local portfolio.
        """
        if not self.portfolio.get_all_assets():
            print("Portfolio is empty")
            return False
        
        symbols = [asset.symbol for asset in self.portfolio.get_all_assets()]
        prices = PriceService.fetch_multiple_prices(symbols, self.currency)
        
        updated_count = 0
        for symbol, price in prices.items():
            if price is not None:
                if self.portfolio.update_asset_price(symbol, price):
                    updated_count += 1
        
        print(f"Updated {updated_count} asset prices")
        return updated_count > 0
    
    def update_single_price(self, symbol: str) -> bool:
        """Update price for single asset."""
        price = PriceService.fetch_crypto_price(symbol, self.currency)
        
        if price is not None:
            return self.portfolio.update_asset_price(symbol, price)
        
        return False
    
    def get_portfolio_analysis(self) -> Dict:
        """
        Get comprehensive portfolio analysis.
        Includes performance metrics and per-asset analysis.
        """
        if not self.portfolio.get_all_assets():
            return {
                'status': 'empty',
                'total_value': 0,
                'total_invested': 0,
                'total_profit_loss': 0,
                'total_profit_loss_percent': 0,
                'assets': []
            }
        
        summary = self.portfolio.get_total_profit_loss()
        
        assets_analysis = []
        for asset in self.portfolio.get_all_assets():
            pl_data = asset.calculate_profit_loss()
            assets_analysis.append({
                'symbol': asset.symbol,
                'quantity': asset.quantity,
                'purchase_price': asset.purchase_price,
                'current_price': asset.current_price,
                'purchase_value': pl_data['purchase_value'],
                'current_value': pl_data['current_value'],
                'profit_loss': pl_data['profit_loss'],
                'profit_loss_percent': pl_data['profit_loss_percent'],
                'purchase_date': asset.purchase_date
            })
        
        return {
            'status': 'ok',
            'portfolio_name': self.portfolio.name,
            'total_assets': len(self.portfolio),
            'total_invested': summary['total_invested'],
            'total_value': summary['total_value'],
            'total_profit_loss': summary['total_profit_loss'],
            'total_profit_loss_percent': summary['total_profit_loss_percent'],
            'assets': assets_analysis,
            'updated_at': datetime.now().isoformat()
        }
    
    def find_best_performers(self, limit: int = 5) -> List[Dict]:
        """Find top performing assets."""
        assets = self.portfolio.get_all_assets()
        
        asset_data = []
        for asset in assets:
            pl_data = asset.calculate_profit_loss()
            asset_data.append({
                'symbol': asset.symbol,
                'profit_loss_percent': pl_data['profit_loss_percent'],
                'profit_loss': pl_data['profit_loss']
            })
        
        return sorted(asset_data, key=lambda x: x['profit_loss_percent'], reverse=True)[:limit]
    
    def find_worst_performers(self, limit: int = 5) -> List[Dict]:
        """Find worst performing assets."""
        assets = self.portfolio.get_all_assets()
        
        asset_data = []
        for asset in assets:
            pl_data = asset.calculate_profit_loss()
            asset_data.append({
                'symbol': asset.symbol,
                'profit_loss_percent': pl_data['profit_loss_percent'],
                'profit_loss': pl_data['profit_loss']
            })
        
        return sorted(asset_data, key=lambda x: x['profit_loss_percent'])[:limit]
    
    def get_allocation(self) -> Dict[str, float]:
        """
        Get portfolio allocation by asset (percentage of total value).
        """
        total_value = self.portfolio.get_total_value()
        
        if total_value == 0:
            return {}
        
        allocation = {}
        for asset in self.portfolio.get_all_assets():
            asset_value = asset.quantity * asset.current_price
            percentage = (asset_value / total_value) * 100
            allocation[asset.symbol] = round(percentage, 2)
        
        return allocation
    
    def search_by_symbol(self, query: str) -> List[Asset]:
        """Search portfolio by symbol."""
        return self.portfolio.search_assets(query)
    
    def generate_report(self) -> str:
        """Generate text report of portfolio."""
        analysis = self.get_portfolio_analysis()
        
        report = []
        report.append("=" * 60)
        report.append(f"PORTFOLIO REPORT - {analysis['portfolio_name']}")
        report.append(f"Generated: {analysis['updated_at']}")
        report.append("=" * 60)
        report.append("")
        
        # Summary
        report.append("SUMMARY")
        report.append("-" * 60)
        report.append(f"Total Assets:          {analysis['total_assets']}")
        report.append(f"Total Invested:        ${analysis['total_invested']:,.2f}")
        report.append(f"Total Value:           ${analysis['total_value']:,.2f}")
        report.append(f"Total Profit/Loss:     ${analysis['total_profit_loss']:,.2f}")
        report.append(f"Total Return:          {analysis['total_profit_loss_percent']:.2f}%")
        report.append("")
        
        # Per-asset details
        report.append("HOLDINGS")
        report.append("-" * 60)
        for asset in analysis['assets']:
            report.append(f"{asset['symbol']:6} | Qty: {asset['quantity']:12.4f} | "
                         f"Cost: ${asset['purchase_value']:10,.2f} | "
                         f"Value: ${asset['current_value']:10,.2f} | "
                         f"P/L: {asset['profit_loss_percent']:+7.2f}%")
        
        report.append("=" * 60)
        return "\n".join(report)


class CurrencyConverter:
    """Convert between different currencies."""
    
    EXCHANGE_RATES = {
        'USD': 1.0,
        'EUR': 0.85,
        'GBP': 0.73,
        'JPY': 110.0,
        'CHF': 0.92,
        'CAD': 1.25,
        'AUD': 1.35,
        'CNY': 6.45,
        'INR': 74.5,
        'MXN': 20.0
    }
    
    @staticmethod
    def convert(amount: float, from_currency: str, to_currency: str) -> Optional[float]:
        """
        Convert amount between currencies.
        Note: This uses static rates. For real app, fetch from API.
        """
        from_curr = from_currency.upper()
        to_curr = to_currency.upper()
        
        if from_curr not in CurrencyConverter.EXCHANGE_RATES:
            print(f"Unknown currency: {from_curr}")
            return None
        
        if to_curr not in CurrencyConverter.EXCHANGE_RATES:
            print(f"Unknown currency: {to_curr}")
            return None
        
        from_rate = CurrencyConverter.EXCHANGE_RATES[from_curr]
        to_rate = CurrencyConverter.EXCHANGE_RATES[to_curr]
        
        converted = amount * (to_rate / from_rate)
        return round(converted, 2)
    
    @staticmethod
    def get_supported_currencies() -> List[str]:
        """Get list of supported currencies."""
        return list(CurrencyConverter.EXCHANGE_RATES.keys())
