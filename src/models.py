"""
Core data models for the price tracker application.
Contains Asset and Portfolio classes using OOP principles.
"""

from datetime import datetime
from typing import List, Dict, Optional


class Asset:
    """
    Represents a single cryptocurrency or stock asset in the portfolio.
    
    Attributes:
        symbol (str): Asset symbol (e.g., 'BTC', 'AAPL')
        quantity (float): Amount of asset owned
        purchase_price (float): Price paid per unit when purchased
        purchase_date (str): Date of purchase (YYYY-MM-DD format)
        current_price (float): Current market price per unit
    """
    
    def __init__(self, symbol: str, quantity: float, purchase_price: float, 
                 purchase_date: str = None, current_price: float = 0.0):
        """Initialize an Asset."""
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        if purchase_price <= 0:
            raise ValueError("Purchase price must be positive")
        if current_price < 0:
            raise ValueError("Current price cannot be negative")
            
        self.symbol = symbol.upper()
        self.quantity = float(quantity)
        self.purchase_price = float(purchase_price)
        self.purchase_date = purchase_date or datetime.now().strftime("%Y-%m-%d")
        self.current_price = float(current_price)
    
    def calculate_profit_loss(self) -> Dict[str, float]:
        """
        Calculate profit or loss for this asset.
        
        Returns:
            Dictionary with:
                - purchase_value: Total amount invested
                - current_value: Current portfolio value of this asset
                - profit_loss: Absolute profit/loss amount
                - profit_loss_percent: Percentage profit/loss
        """
        purchase_value = self.quantity * self.purchase_price
        current_value = self.quantity * self.current_price
        profit_loss = current_value - purchase_value
        
        # Avoid division by zero
        profit_loss_percent = (profit_loss / purchase_value * 100) if purchase_value != 0 else 0
        
        return {
            'purchase_value': round(purchase_value, 2),
            'current_value': round(current_value, 2),
            'profit_loss': round(profit_loss, 2),
            'profit_loss_percent': round(profit_loss_percent, 2)
        }
    
    def to_dict(self) -> Dict:
        """Convert asset to dictionary for JSON serialization."""
        return {
            'symbol': self.symbol,
            'quantity': self.quantity,
            'purchase_price': self.purchase_price,
            'purchase_date': self.purchase_date,
            'current_price': self.current_price
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Asset':
        """Create Asset from dictionary (from JSON)."""
        return cls(
            symbol=data['symbol'],
            quantity=data['quantity'],
            purchase_price=data['purchase_price'],
            purchase_date=data.get('purchase_date'),
            current_price=data.get('current_price', 0.0)
        )
    
    def __str__(self) -> str:
        """String representation of Asset."""
        return f"{self.symbol}: {self.quantity} units @ ${self.current_price:.2f}"
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"Asset('{self.symbol}', {self.quantity}, ${self.purchase_price:.2f})"


class Portfolio:
    """
    Manages a collection of assets.
    Demonstrates inheritance-like behavior through composition.
    
    Attributes:
        assets (List[Asset]): List of assets in portfolio
        name (str): Portfolio identifier/name
    """
    
    def __init__(self, name: str = "My Portfolio"):
        """Initialize an empty portfolio."""
        self.name = name
        self._assets: Dict[str, Asset] = {}  # symbol -> Asset mapping
    
    def add_asset(self, asset: Asset) -> None:
        """
        Add an asset to the portfolio.
        If asset exists, it updates the quantity (combines holdings).
        """
        if asset.symbol in self._assets:
            existing = self._assets[asset.symbol]
            # Combine holdings - weighted average purchase price
            total_quantity = existing.quantity + asset.quantity
            weighted_price = (
                (existing.quantity * existing.purchase_price + 
                 asset.quantity * asset.purchase_price) / total_quantity
            )
            existing.quantity = total_quantity
            existing.purchase_price = weighted_price
            existing.current_price = asset.current_price
        else:
            self._assets[asset.symbol] = asset
    
    def remove_asset(self, symbol: str) -> bool:
        """
        Remove an asset from portfolio by symbol.
        Returns True if removed, False if not found.
        """
        if symbol.upper() in self._assets:
            del self._assets[symbol.upper()]
            return True
        return False
    
    def get_asset(self, symbol: str) -> Optional[Asset]:
        """Get a specific asset by symbol."""
        return self._assets.get(symbol.upper())
    
    def get_all_assets(self) -> List[Asset]:
        """Return list of all assets in portfolio."""
        return list(self._assets.values())
    
    def get_total_value(self) -> float:
        """Calculate total current value of portfolio."""
        return sum(asset.quantity * asset.current_price for asset in self._assets.values())
    
    def get_total_purchase_value(self) -> float:
        """Calculate total amount invested."""
        return sum(
            asset.quantity * asset.purchase_price 
            for asset in self._assets.values()
        )
    
    def get_total_profit_loss(self) -> Dict[str, float]:
        """
        Calculate total profit/loss for entire portfolio.
        
        Returns:
            Dictionary with total metrics and per-asset breakdown
        """
        total_purchase = self.get_total_purchase_value()
        total_current = self.get_total_value()
        total_profit_loss = total_current - total_purchase
        
        total_percent = (
            (total_profit_loss / total_purchase * 100) 
            if total_purchase != 0 else 0
        )
        
        return {
            'total_invested': round(total_purchase, 2),
            'total_value': round(total_current, 2),
            'total_profit_loss': round(total_profit_loss, 2),
            'total_profit_loss_percent': round(total_percent, 2)
        }
    
    def search_assets(self, query: str) -> List[Asset]:
        """Search assets by partial symbol match (case-insensitive)."""
        query_upper = query.upper()
        return [
            asset for asset in self._assets.values()
            if query_upper in asset.symbol
        ]
    
    def get_portfolio_summary(self) -> Dict:
        """Get comprehensive portfolio summary."""
        summary = {
            'portfolio_name': self.name,
            'total_assets': len(self._assets),
            'total_value': self.get_total_value(),
            'total_invested': self.get_total_purchase_value(),
            'total_profit_loss': self.get_total_profit_loss(),
            'assets': [asset.to_dict() for asset in self._assets.values()]
        }
        return summary
    
    def update_asset_price(self, symbol: str, new_price: float) -> bool:
        """Update current price of an asset."""
        asset = self.get_asset(symbol)
        if asset:
            asset.current_price = float(new_price)
            return True
        return False
    
    def clear(self) -> None:
        """Clear all assets from portfolio."""
        self._assets.clear()
    
    def __len__(self) -> int:
        """Return number of unique assets."""
        return len(self._assets)
    
    def __str__(self) -> str:
        """String representation."""
        return f"Portfolio '{self.name}' with {len(self._assets)} assets"
    
    def __iter__(self):
        """Make portfolio iterable."""
        return iter(self._assets.values())
    
    def to_dict(self) -> Dict:
        """Convert portfolio to dictionary."""
        return {
            'name': self.name,
            'assets': [asset.to_dict() for asset in self._assets.values()]
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Portfolio':
        """Create Portfolio from dictionary."""
        portfolio = cls(data.get('name', 'My Portfolio'))
        for asset_data in data.get('assets', []):
            asset = Asset.from_dict(asset_data)
            portfolio.add_asset(asset)
        return portfolio
