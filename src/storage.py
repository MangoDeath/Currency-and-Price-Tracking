"""
Storage module for file persistence.
Handles JSON and CSV file operations for portfolio data.
"""

import json
import csv
import os
from typing import Optional, List, Dict
from models import Portfolio, Asset
from datetime import datetime


class StorageError(Exception):
    """Custom exception for storage errors."""
    pass


class JsonStorage:
    """Handles JSON file persistence for portfolio data."""
    
    def __init__(self, filepath: str):
        """Initialize storage with file path."""
        self.filepath = filepath
        self._ensure_directory_exists()
    
    def _ensure_directory_exists(self) -> None:
        """Ensure directory exists for file."""
        directory = os.path.dirname(self.filepath)
        if directory and not os.path.exists(directory):
            try:
                os.makedirs(directory)
            except OSError as e:
                raise StorageError(f"Failed to create directory: {e}")
    
    def save_portfolio(self, portfolio: Portfolio) -> bool:
        """
        Save portfolio to JSON file.
        Returns True on success, False otherwise.
        """
        try:
            data = portfolio.to_dict()
            with open(self.filepath, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Portfolio saved to {self.filepath}")
            return True
        except IOError as e:
            raise StorageError(f"Failed to save portfolio: {e}")
        except Exception as e:
            raise StorageError(f"Unexpected error saving portfolio: {e}")
    
    def load_portfolio(self) -> Optional[Portfolio]:
        """
        Load portfolio from JSON file.
        Returns Portfolio object or None if file doesn't exist.
        """
        if not os.path.exists(self.filepath):
            print(f"Portfolio file not found: {self.filepath}")
            return None
        
        try:
            with open(self.filepath, 'r') as f:
                data = json.load(f)
            portfolio = Portfolio.from_dict(data)
            print(f"Portfolio loaded from {self.filepath}")
            return portfolio
        except json.JSONDecodeError as e:
            raise StorageError(f"Invalid JSON format: {e}")
        except IOError as e:
            raise StorageError(f"Failed to read portfolio file: {e}")
        except Exception as e:
            raise StorageError(f"Unexpected error loading portfolio: {e}")
    
    def delete_file(self) -> bool:
        """Delete the portfolio file."""
        try:
            if os.path.exists(self.filepath):
                os.remove(self.filepath)
                print(f"Portfolio file deleted: {self.filepath}")
                return True
            return False
        except OSError as e:
            raise StorageError(f"Failed to delete file: {e}")
    
    def file_exists(self) -> bool:
        """Check if portfolio file exists."""
        return os.path.exists(self.filepath)


class CsvExport:
    """Handles CSV export of portfolio data."""
    
    @staticmethod
    def export_portfolio(portfolio: Portfolio, filepath: str) -> bool:
        """
        Export portfolio to CSV file.
        CSV format: Symbol, Quantity, Purchase Price, Purchase Date, Current Price, Current Value, Profit/Loss
        """
        try:
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow([
                    'Symbol', 'Quantity', 'Purchase Price', 'Purchase Date',
                    'Current Price', 'Current Value', 'Profit/Loss', 'Profit/Loss %'
                ])
                
                # Write asset data
                for asset in portfolio.get_all_assets():
                    pl_data = asset.calculate_profit_loss()
                    writer.writerow([
                        asset.symbol,
                        f"{asset.quantity:.8f}".rstrip('0').rstrip('.'),
                        f"{asset.purchase_price:.8f}".rstrip('0').rstrip('.'),
                        asset.purchase_date,
                        f"{asset.current_price:.8f}".rstrip('0').rstrip('.'),
                        f"{pl_data['current_value']:.2f}",
                        f"{pl_data['profit_loss']:.2f}",
                        f"{pl_data['profit_loss_percent']:.2f}%"
                    ])
                
                # Write summary
                summary = portfolio.get_total_profit_loss()
                writer.writerow([])  # Empty row
                writer.writerow(['SUMMARY'])
                writer.writerow(['Total Invested', f"${summary['total_invested']:.2f}"])
                writer.writerow(['Total Value', f"${summary['total_value']:.2f}"])
                writer.writerow(['Total Profit/Loss', f"${summary['total_profit_loss']:.2f}"])
                writer.writerow(['Total Return %', f"{summary['total_profit_loss_percent']:.2f}%"])
                
                print(f"Portfolio exported to CSV: {filepath}")
                return True
        except IOError as e:
            raise StorageError(f"Failed to export CSV: {e}")
    
    @staticmethod
    def export_price_history(prices_data: List[Dict], filepath: str) -> bool:
        """
        Export price history to CSV.
        Useful for tracking price changes over time.
        """
        try:
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                
                if not prices_data:
                    return True
                
                # Write header from first record keys
                writer.writerow(prices_data[0].keys())
                
                # Write data rows
                for record in prices_data:
                    writer.writerow(record.values())
                
                print(f"Price history exported to CSV: {filepath}")
                return True
        except IOError as e:
            raise StorageError(f"Failed to export price history: {e}")
    
    @staticmethod
    def import_from_csv(filepath: str) -> Optional[Portfolio]:
        """
        Import portfolio from CSV file.
        Expected format: Symbol, Quantity, Purchase Price, Purchase Date
        """
        if not os.path.exists(filepath):
            raise StorageError(f"CSV file not found: {filepath}")
        
        try:
            portfolio = Portfolio(name="Imported Portfolio")
            
            with open(filepath, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        asset = Asset(
                            symbol=row['Symbol'],
                            quantity=float(row['Quantity']),
                            purchase_price=float(row['Purchase Price']),
                            purchase_date=row.get('Purchase Date', datetime.now().strftime("%Y-%m-%d")),
                            current_price=float(row.get('Current Price', 0))
                        )
                        portfolio.add_asset(asset)
                    except (ValueError, KeyError) as e:
                        print(f"Warning: Skipping invalid row: {row} ({e})")
                        continue
            
            print(f"Portfolio imported from CSV: {filepath}")
            return portfolio
        except IOError as e:
            raise StorageError(f"Failed to import CSV: {e}")


class BackupManager:
    """Manages portfolio backups."""
    
    def __init__(self, base_path: str):
        """Initialize backup manager with base path."""
        self.base_path = base_path
        self.backup_dir = os.path.join(base_path, 'backups')
        self._ensure_directory_exists()
    
    def _ensure_directory_exists(self) -> None:
        """Ensure backup directory exists."""
        if not os.path.exists(self.backup_dir):
            try:
                os.makedirs(self.backup_dir)
            except OSError as e:
                raise StorageError(f"Failed to create backup directory: {e}")
    
    def create_backup(self, portfolio: Portfolio) -> str:
        """
        Create timestamped backup of portfolio.
        Returns backup filename.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(self.backup_dir, f"portfolio_backup_{timestamp}.json")
        
        try:
            storage = JsonStorage(backup_file)
            storage.save_portfolio(portfolio)
            print(f"Backup created: {backup_file}")
            return backup_file
        except StorageError as e:
            raise StorageError(f"Failed to create backup: {e}")
    
    def list_backups(self) -> List[str]:
        """List all available backups."""
        try:
            backups = []
            for filename in os.listdir(self.backup_dir):
                if filename.startswith('portfolio_backup_') and filename.endswith('.json'):
                    backups.append(os.path.join(self.backup_dir, filename))
            return sorted(backups, reverse=True)
        except OSError as e:
            raise StorageError(f"Failed to list backups: {e}")
    
    def restore_backup(self, backup_file: str) -> Optional[Portfolio]:
        """Restore portfolio from backup file."""
        try:
            storage = JsonStorage(backup_file)
            portfolio = storage.load_portfolio()
            print(f"Portfolio restored from backup: {backup_file}")
            return portfolio
        except StorageError as e:
            raise StorageError(f"Failed to restore backup: {e}")
