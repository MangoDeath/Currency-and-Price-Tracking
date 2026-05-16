"""
Input validation module using Regular Expressions.
Validates user input for asset symbols, prices, and other data.
"""

import re
from typing import Tuple, Optional


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class InputValidator:
    """Validates user input using regex patterns and type checking."""
    
    # Regex patterns
    SYMBOL_PATTERN = r'^[A-Z]{1,10}$'  # 1-10 uppercase letters
    PRICE_PATTERN = r'^\d+(\.\d{1,8})?$'  # Positive numbers with up to 8 decimals
    QUANTITY_PATTERN = r'^\d+(\.\d{1,8})?$'  # Positive numbers with decimals
    DATE_PATTERN = r'^\d{4}-\d{2}-\d{2}$'  # YYYY-MM-DD format
    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    @staticmethod
    def validate_symbol(symbol: str) -> bool:
        """
        Validate asset symbol (e.g., BTC, AAPL).
        Rules: 1-10 uppercase letters only.
        """
        if not isinstance(symbol, str):
            return False
        return bool(re.match(InputValidator.SYMBOL_PATTERN, symbol.strip()))
    
    @staticmethod
    def validate_price(price_str: str) -> bool:
        """
        Validate price input.
        Rules: Positive number with up to 8 decimal places.
        """
        if not isinstance(price_str, str):
            return False
        
        price_str = price_str.strip()
        if not re.match(InputValidator.PRICE_PATTERN, price_str):
            return False
        
        try:
            price = float(price_str)
            return price > 0
        except ValueError:
            return False
    
    @staticmethod
    def validate_quantity(quantity_str: str) -> bool:
        """
        Validate quantity input.
        Rules: Positive number with up to 8 decimal places.
        """
        if not isinstance(quantity_str, str):
            return False
        
        quantity_str = quantity_str.strip()
        if not re.match(InputValidator.QUANTITY_PATTERN, quantity_str):
            return False
        
        try:
            quantity = float(quantity_str)
            return quantity > 0
        except ValueError:
            return False
    
    @staticmethod
    def validate_date(date_str: str) -> bool:
        """
        Validate date format (YYYY-MM-DD).
        Does NOT validate if date is realistic, only format.
        """
        if not isinstance(date_str, str):
            return False
        
        return bool(re.match(InputValidator.DATE_PATTERN, date_str.strip()))
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        if not isinstance(email, str):
            return False
        return bool(re.match(InputValidator.EMAIL_PATTERN, email.strip()))
    
    @staticmethod
    def sanitize_symbol(symbol: str) -> str:
        """
        Sanitize and normalize symbol.
        Converts to uppercase and removes whitespace.
        """
        sanitized = symbol.strip().upper()
        # Remove any non-letter characters
        sanitized = re.sub(r'[^A-Z]', '', sanitized)
        return sanitized
    
    @staticmethod
    def extract_numbers(text: str) -> list:
        """Extract all numbers from text using regex."""
        return re.findall(r'\d+(\.\d+)?', text)
    
    @staticmethod
    def validate_csv_line(line: str, expected_fields: int) -> bool:
        """Validate CSV line has correct number of fields."""
        fields = line.split(',')
        return len(fields) == expected_fields
    
    @staticmethod
    def validate_input_batch(inputs: dict) -> Tuple[bool, list]:
        """
        Validate multiple inputs at once.
        Returns: (is_valid, list_of_errors)
        """
        errors = []
        
        if 'symbol' in inputs and not InputValidator.validate_symbol(inputs['symbol']):
            errors.append(f"Invalid symbol: '{inputs['symbol']}'. Use 1-10 uppercase letters.")
        
        if 'price' in inputs and not InputValidator.validate_price(str(inputs['price'])):
            errors.append(f"Invalid price: '{inputs['price']}'. Must be a positive number.")
        
        if 'quantity' in inputs and not InputValidator.validate_quantity(str(inputs['quantity'])):
            errors.append(f"Invalid quantity: '{inputs['quantity']}'. Must be a positive number.")
        
        if 'date' in inputs and not InputValidator.validate_date(inputs['date']):
            errors.append(f"Invalid date: '{inputs['date']}'. Use YYYY-MM-DD format.")
        
        return len(errors) == 0, errors


class SymbolValidator:
    """Specialized validator for cryptocurrency/stock symbols."""
    
    # Known symbols (can be extended)
    KNOWN_CRYPTO = {
        'BTC', 'ETH', 'BNB', 'XRP', 'ADA', 'SOL', 'DOT', 'DOGE', 'SHIB', 'LINK',
        'MATIC', 'AVAX', 'ARB', 'OP', 'LTC', 'BCH', 'XMR', 'ZEC', 'ATOM', 'ALGO'
    }
    
    KNOWN_STOCKS = {
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'JPM', 'V', 'JNJ',
        'WMT', 'PG', 'MA', 'HD', 'MCD', 'DIS', 'KO', 'IBM', 'INTC', 'AMD'
    }
    
    @classmethod
    def is_known_crypto(cls, symbol: str) -> bool:
        """Check if symbol is a known cryptocurrency."""
        return symbol.upper() in cls.KNOWN_CRYPTO
    
    @classmethod
    def is_known_stock(cls, symbol: str) -> bool:
        """Check if symbol is a known stock."""
        return symbol.upper() in cls.KNOWN_STOCKS
    
    @classmethod
    def get_suggestions(cls, partial: str, max_suggestions: int = 5) -> list:
        """Get symbol suggestions based on partial input."""
        partial_upper = partial.upper()
        all_symbols = cls.KNOWN_CRYPTO | cls.KNOWN_STOCKS
        
        matches = [s for s in all_symbols if s.startswith(partial_upper)]
        return sorted(matches)[:max_suggestions]
