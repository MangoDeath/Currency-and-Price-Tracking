"""
Tkinter GUI for Crypto/Stock Price Tracker
Main user interface for the application.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from datetime import datetime
import os
import sys
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# Add src directory to path
sys.path.insert(0, os.path.dirname(__file__))

from models import Asset, Portfolio
from services import PriceService, PortfolioService, CurrencyConverter
from storage import JsonStorage, CsvExport, BackupManager
from validators import InputValidator, ValidationError


class PriceTrackerGUI:
    """Main GUI application for price tracking."""
    
    def __init__(self, root: tk.Tk):
        """Initialize the GUI application."""
        self.root = root
        self.root.title("Crypto/Stock Price Tracker")
        self.root.geometry("1200x700")
        
        # Initialize data
        self.portfolio = Portfolio("My Investments")
        self.service = PortfolioService(self.portfolio, currency='usd')
        self.storage = JsonStorage("data/portfolio.json")
        self.backup_manager = BackupManager("data")
        self.usdt_prices = {}
        self.usdt_prices_updated_at = None
        
        # Load existing portfolio
        loaded = self.storage.load_portfolio()
        if loaded:
            self.portfolio = loaded
            self.service = PortfolioService(self.portfolio, currency='usd')
        
        # Threading
        self.update_thread = None
        self.is_running = True
        
        # Build GUI
        self._build_gui()
        
        # Start auto-update thread
        self._start_auto_update()
        self._start_usdt_price_update()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _build_gui(self):
        """Build the GUI components."""
        # Create main frames
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create tabs
        self._create_dashboard_tab()
        self._create_portfolio_tab()
        self._create_add_asset_tab()
        self._create_analysis_tab()
        self._create_settings_tab()
    
    def _create_dashboard_tab(self):
        """Create dashboard tab with summary."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Dashboard")
        
        # Title
        title_label = ttk.Label(tab, text="Portfolio Summary", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Summary frame
        summary_frame = ttk.LabelFrame(tab, text="Portfolio Overview", padding=10)
        summary_frame.pack(fill=tk.X, expand=False, padx=10, pady=10)
        
        # Create grid of summary items
        grid_frame = ttk.Frame(summary_frame)
        grid_frame.pack(fill=tk.X, expand=False)
        grid_frame.columnconfigure(1, weight=1)
        
        # Total value
        ttk.Label(grid_frame, text="Total Portfolio Value:", 
                 font=("Arial", 11, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.total_value_label = ttk.Label(grid_frame, text="$0.00", 
                                          font=("Arial", 12), foreground="green")
        self.total_value_label.grid(row=0, column=1, sticky=tk.E, padx=20)
        
        # Total invested
        ttk.Label(grid_frame, text="Total Invested:", 
                 font=("Arial", 11, "bold")).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.total_invested_label = ttk.Label(grid_frame, text="$0.00", 
                                             font=("Arial", 12))
        self.total_invested_label.grid(row=1, column=1, sticky=tk.E, padx=20)
        
        # Total profit/loss
        ttk.Label(grid_frame, text="Total Profit/Loss:", 
                 font=("Arial", 11, "bold")).grid(row=2, column=0, sticky=tk.W, pady=5)
        self.total_pl_label = ttk.Label(grid_frame, text="$0.00", 
                                       font=("Arial", 12), foreground="red")
        self.total_pl_label.grid(row=2, column=1, sticky=tk.E, padx=20)
        
        # Return percentage
        ttk.Label(grid_frame, text="Total Return:", 
                 font=("Arial", 11, "bold")).grid(row=3, column=0, sticky=tk.W, pady=5)
        self.total_percent_label = ttk.Label(grid_frame, text="0.00%", 
                                            font=("Arial", 12), foreground="blue")
        self.total_percent_label.grid(row=3, column=1, sticky=tk.E, padx=20)

        # USDT price table
        prices_frame = ttk.LabelFrame(tab, text="Coin Prices in USDT", padding=10)
        prices_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.usdt_prices_status_label = ttk.Label(
            prices_frame,
            text="Loading USDT prices...",
            font=("Arial", 9)
        )
        self.usdt_prices_status_label.pack(anchor=tk.W, pady=(0, 6))

        prices_tree_frame = ttk.Frame(prices_frame)
        prices_tree_frame.pack(fill=tk.BOTH, expand=True)

        prices_scrollbar = ttk.Scrollbar(prices_tree_frame)
        prices_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        price_columns = ("Symbol", "Price (USDT)")
        self.usdt_price_tree = ttk.Treeview(
            prices_tree_frame,
            columns=price_columns,
            show="headings",
            height=12,
            yscrollcommand=prices_scrollbar.set
        )
        prices_scrollbar.config(command=self.usdt_price_tree.yview)

        self.usdt_price_tree.heading("Symbol", text="Symbol")
        self.usdt_price_tree.heading("Price (USDT)", text="Price (USDT)")
        self.usdt_price_tree.column("Symbol", width=120, anchor=tk.CENTER)
        self.usdt_price_tree.column("Price (USDT)", width=180, anchor=tk.E)
        self.usdt_price_tree.pack(fill=tk.BOTH, expand=True)
        
        # Button frame
        button_frame = ttk.Frame(tab)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="Refresh Prices", 
                  command=self._refresh_prices).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Create Backup", 
                  command=self._create_backup).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Export to CSV", 
                  command=self._export_csv).pack(side=tk.LEFT, padx=5)
    
    def _create_portfolio_tab(self):
        """Create portfolio tab with holdings list."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Portfolio")
        
        # Title
        title_label = ttk.Label(tab, text="Your Holdings", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Tree view for holdings
        columns = ("Symbol", "Quantity", "Purchase Price", "Current Price", 
                   "Current Value", "Profit/Loss", "Return %")
        
        tree_frame = ttk.Frame(tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Treeview
        self.portfolio_tree = ttk.Treeview(tree_frame, columns=columns, 
                                          height=15, yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.portfolio_tree.yview)
        
        # Define column headings
        self.portfolio_tree.heading("#0", text="")
        self.portfolio_tree.column("#0", width=0)
        
        for col in columns:
            self.portfolio_tree.heading(col, text=col)
            self.portfolio_tree.column(col, width=120, anchor=tk.CENTER)
        
        self.portfolio_tree.pack(fill=tk.BOTH, expand=True)
        
        # Button frame
        button_frame = ttk.Frame(tab)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="Remove Selected", 
                  command=self._remove_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Update Prices", 
                  command=self._refresh_prices).pack(side=tk.LEFT, padx=5)
        
        self._update_portfolio_display()
    
    def _create_add_asset_tab(self):
        """Create tab for adding new assets."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Add Asset")
        
        # Title
        title_label = ttk.Label(tab, text="Add New Asset to Portfolio", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Form frame
        form_frame = ttk.LabelFrame(tab, text="Asset Details", padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Symbol
        ttk.Label(form_frame, text="Asset Symbol:", 
                 font=("Arial", 11)).grid(row=0, column=0, sticky=tk.W, pady=10)
        self.symbol_entry = ttk.Entry(form_frame, width=20, font=("Arial", 11))
        self.symbol_entry.grid(row=0, column=1, sticky=tk.W, padx=20)
        ttk.Label(form_frame, text="(e.g., BTC, ETH, AAPL)", 
                 font=("Arial", 9)).grid(row=0, column=2, sticky=tk.W)
        
        # Quantity
        ttk.Label(form_frame, text="Quantity:", 
                 font=("Arial", 11)).grid(row=1, column=0, sticky=tk.W, pady=10)
        self.quantity_entry = ttk.Entry(form_frame, width=20, font=("Arial", 11))
        self.quantity_entry.grid(row=1, column=1, sticky=tk.W, padx=20)
        
        # Purchase Price
        ttk.Label(form_frame, text="Purchase Price ($):", 
                 font=("Arial", 11)).grid(row=2, column=0, sticky=tk.W, pady=10)
        self.price_entry = ttk.Entry(form_frame, width=20, font=("Arial", 11))
        self.price_entry.grid(row=2, column=1, sticky=tk.W, padx=20)
        
        # Purchase Date
        ttk.Label(form_frame, text="Purchase Date:", 
                 font=("Arial", 11)).grid(row=3, column=0, sticky=tk.W, pady=10)
        self.date_entry = ttk.Entry(form_frame, width=20, font=("Arial", 11))
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.grid(row=3, column=1, sticky=tk.W, padx=20)
        ttk.Label(form_frame, text="(YYYY-MM-DD)", 
                 font=("Arial", 9)).grid(row=3, column=2, sticky=tk.W)
        
        # Button frame
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=4, column=0, columnspan=3, sticky=tk.W, pady=20)
        
        ttk.Button(button_frame, text="Add Asset", 
                  command=self._add_asset).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear", 
                  command=self._clear_form).pack(side=tk.LEFT, padx=5)
        
        # Info
        info_frame = ttk.LabelFrame(tab, text="Supported Cryptos", padding=10)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        info_text = ttk.Label(info_frame, text=self._get_supported_cryptos_text(), 
                             font=("Arial", 9), justify=tk.LEFT)
        info_text.pack()
    
    def _create_analysis_tab(self):
        """Create tab for portfolio analysis with charts and data."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Analysis")
        
        # Title
        title_label = ttk.Label(tab, text="Portfolio Analysis & Visualizations", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Create notebook for sub-tabs
        analysis_notebook = ttk.Notebook(tab)
        analysis_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Charts frame
        charts_frame = ttk.Frame(analysis_notebook)
        analysis_notebook.add(charts_frame, text="Charts")
        
        # Create a frame for charts
        self.charts_container = ttk.Frame(charts_frame)
        self.charts_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top performers
        top_frame = ttk.Frame(analysis_notebook)
        analysis_notebook.add(top_frame, text="Top Performers")
        
        ttk.Label(top_frame, text="Best Performing Assets", 
                 font=("Arial", 12, "bold")).pack(pady=10)
        
        columns = ("Symbol", "Return %", "Profit/Loss")
        self.top_tree = ttk.Treeview(top_frame, columns=columns, height=10)
        
        for col in columns:
            self.top_tree.heading(col, text=col)
            self.top_tree.column(col, width=200, anchor=tk.CENTER)
        
        self.top_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Worst performers
        worst_frame = ttk.Frame(analysis_notebook)
        analysis_notebook.add(worst_frame, text="Worst Performers")
        
        ttk.Label(worst_frame, text="Worst Performing Assets", 
                 font=("Arial", 12, "bold")).pack(pady=10)
        
        self.worst_tree = ttk.Treeview(worst_frame, columns=columns, height=10)
        
        for col in columns:
            self.worst_tree.heading(col, text=col)
            self.worst_tree.column(col, width=200, anchor=tk.CENTER)
        
        self.worst_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Allocation
        alloc_frame = ttk.Frame(analysis_notebook)
        analysis_notebook.add(alloc_frame, text="Allocation")
        
        ttk.Label(alloc_frame, text="Portfolio Allocation", 
                 font=("Arial", 12, "bold")).pack(pady=10)
        
        columns = ("Symbol", "Allocation %")
        self.alloc_tree = ttk.Treeview(alloc_frame, columns=columns, height=15)
        
        for col in columns:
            self.alloc_tree.heading(col, text=col)
            self.alloc_tree.column(col, width=300, anchor=tk.CENTER)
        
        self.alloc_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self._update_analysis_display()
    
    def _create_settings_tab(self):
        """Create settings tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Settings")
        
        # Title
        title_label = ttk.Label(tab, text="Settings", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Currency setting
        settings_frame = ttk.LabelFrame(tab, text="Preferences", padding=20)
        settings_frame.pack(fill=tk.BOTH, expand=False, padx=20, pady=20)
        
        ttk.Label(settings_frame, text="Currency:", 
                 font=("Arial", 11)).grid(row=0, column=0, sticky=tk.W, pady=10)
        
        self.currency_var = tk.StringVar(value="USD")
        currency_combo = ttk.Combobox(settings_frame, 
                                     textvariable=self.currency_var,
                                     values=CurrencyConverter.get_supported_currencies(),
                                     state="readonly", width=10)
        currency_combo.grid(row=0, column=1, sticky=tk.W, padx=20)
        
        # Portfolio name
        ttk.Label(settings_frame, text="Portfolio Name:", 
                 font=("Arial", 11)).grid(row=1, column=0, sticky=tk.W, pady=10)
        
        self.portfolio_name_entry = ttk.Entry(settings_frame, width=30, 
                                             font=("Arial", 11))
        self.portfolio_name_entry.insert(0, self.portfolio.name)
        self.portfolio_name_entry.grid(row=1, column=1, sticky=tk.W, padx=20)
        
        # Buttons
        button_frame = ttk.Frame(settings_frame)
        button_frame.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=20)
        
        ttk.Button(button_frame, text="Save Settings", 
                  command=self._save_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Export Report", 
                  command=self._export_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear Portfolio", 
                  command=self._clear_portfolio).pack(side=tk.LEFT, padx=5)
        
        # Backup management
        backup_frame = ttk.LabelFrame(tab, text="Backup Management", padding=20)
        backup_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        ttk.Button(backup_frame, text="Create Backup", 
                  command=self._create_backup).pack(side=tk.LEFT, padx=5)
        ttk.Button(backup_frame, text="List Backups", 
                  command=self._list_backups).pack(side=tk.LEFT, padx=5)
    
    def _add_asset(self):
        """Add new asset to portfolio."""
        try:
            symbol = self.symbol_entry.get().strip().upper()
            quantity_str = self.quantity_entry.get().strip()
            price_str = self.price_entry.get().strip()
            date_str = self.date_entry.get().strip()
            
            # Validate inputs
            if not InputValidator.validate_symbol(symbol):
                messagebox.showerror("Invalid Symbol", 
                                   "Symbol must be 1-10 uppercase letters")
                return
            
            if not InputValidator.validate_quantity(quantity_str):
                messagebox.showerror("Invalid Quantity", 
                                   "Quantity must be a positive number")
                return
            
            if not InputValidator.validate_price(price_str):
                messagebox.showerror("Invalid Price", 
                                   "Price must be a positive number")
                return
            
            if not InputValidator.validate_date(date_str):
                messagebox.showerror("Invalid Date", 
                                   "Date must be in YYYY-MM-DD format")
                return
            
            # Create and add asset
            asset = Asset(
                symbol=symbol,
                quantity=float(quantity_str),
                purchase_price=float(price_str),
                purchase_date=date_str
            )
            
            # Fetch current price
            current_price = PriceService.fetch_crypto_price(symbol)
            if current_price:
                asset.current_price = current_price
            
            self.portfolio.add_asset(asset)
            
            # Save and update display
            self.storage.save_portfolio(self.portfolio)
            self._clear_form()
            self._update_portfolio_display()
            self._update_dashboard()
            
            messagebox.showinfo("Success", f"Asset {symbol} added successfully!")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add asset: {str(e)}")
    
    def _remove_selected(self):
        """Remove selected asset from portfolio."""
        selected = self.portfolio_tree.selection()
        
        if not selected:
            messagebox.showwarning("No Selection", "Please select an asset to remove")
            return
        
        item = selected[0]
        symbol = self.portfolio_tree.item(item)['values'][0]
        
        if messagebox.askyesno("Confirm", f"Remove {symbol} from portfolio?"):
            if self.portfolio.remove_asset(symbol):
                self.storage.save_portfolio(self.portfolio)
                self._update_portfolio_display()
                self._update_dashboard()
                messagebox.showinfo("Success", f"Asset {symbol} removed!")
    
    def _refresh_prices(self):
        """Refresh all asset prices."""
        messagebox.showinfo("Refreshing", "Updating prices from API...")
        
        def update_in_thread():
            try:
                portfolio_updated = self.service.update_all_prices()
                market_updated = self._load_usdt_prices()

                if portfolio_updated:
                    self.storage.save_portfolio(self.portfolio)

                def finish_update():
                    if portfolio_updated:
                        self._update_portfolio_display()

                    if portfolio_updated or market_updated:
                        self._update_dashboard()
                        self._update_usdt_prices_display()
                        self._update_analysis_display()
                        messagebox.showinfo("Success", "Prices updated successfully!")
                    else:
                        messagebox.showwarning("No Update", "No prices were updated")

                self.root.after(0, finish_update)
            except Exception as e:
                error_message = str(e)
                self.root.after(
                    0,
                    lambda message=error_message: messagebox.showerror(
                        "Error",
                        f"Failed to update prices: {message}"
                    )
                )
        
        thread = threading.Thread(target=update_in_thread, daemon=True)
        thread.start()

    def _load_usdt_prices(self) -> bool:
        """Fetch all supported crypto prices expressed in USDT."""
        symbols = list(PriceService.get_supported_cryptos().keys())
        self.usdt_prices = PriceService.fetch_prices_in_usdt(symbols)
        self.usdt_prices_updated_at = datetime.now()
        return any(price is not None for price in self.usdt_prices.values())

    def _start_usdt_price_update(self):
        """Load the dashboard USDT price table without blocking the UI."""
        def update_in_thread():
            try:
                self._load_usdt_prices()
                self.root.after(0, self._update_usdt_prices_display)
            except Exception as e:
                print(f"USDT price update error: {e}")

        thread = threading.Thread(target=update_in_thread, daemon=True)
        thread.start()
    
    def _export_csv(self):
        """Export portfolio to CSV."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"portfolio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        
        if file_path:
            try:
                CsvExport.export_portfolio(self.portfolio, file_path)
                messagebox.showinfo("Success", f"Portfolio exported to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export CSV: {str(e)}")
    
    def _create_backup(self):
        """Create portfolio backup."""
        try:
            backup_file = self.backup_manager.create_backup(self.portfolio)
            messagebox.showinfo("Success", f"Backup created:\n{backup_file}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create backup: {str(e)}")
    
    def _list_backups(self):
        """List available backups."""
        try:
            backups = self.backup_manager.list_backups()
            
            if not backups:
                messagebox.showinfo("Backups", "No backups found")
                return
            
            backup_list = "\n".join([os.path.basename(b) for b in backups[:10]])
            messagebox.showinfo("Available Backups", backup_list)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to list backups: {str(e)}")
    
    def _clear_form(self):
        """Clear input form."""
        self.symbol_entry.delete(0, tk.END)
        self.quantity_entry.delete(0, tk.END)
        self.price_entry.delete(0, tk.END)
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
    
    def _save_settings(self):
        """Save settings."""
        portfolio_name = self.portfolio_name_entry.get().strip()
        
        if not portfolio_name:
            messagebox.showwarning("Invalid", "Portfolio name cannot be empty")
            return
        
        self.portfolio.name = portfolio_name
        self.storage.save_portfolio(self.portfolio)
        messagebox.showinfo("Success", "Settings saved!")
    
    def _export_report(self):
        """Export portfolio report."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        
        if file_path:
            try:
                report = self.service.generate_report()
                with open(file_path, 'w') as f:
                    f.write(report)
                messagebox.showinfo("Success", f"Report exported to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export report: {str(e)}")
    
    def _clear_portfolio(self):
        """Clear entire portfolio."""
        if messagebox.askyesno("Confirm", "Clear entire portfolio? This cannot be undone!"):
            self.portfolio.clear()
            self.storage.save_portfolio(self.portfolio)
            self._update_portfolio_display()
            self._update_dashboard()
            messagebox.showinfo("Success", "Portfolio cleared!")
    
    def _update_portfolio_display(self):
        """Update portfolio tree view."""
        # Clear existing items
        for item in self.portfolio_tree.get_children():
            self.portfolio_tree.delete(item)
        
        # Add assets
        for asset in self.portfolio.get_all_assets():
            pl_data = asset.calculate_profit_loss()
            color = "green" if pl_data['profit_loss'] >= 0 else "red"
            
            self.portfolio_tree.insert("", tk.END, values=(
                asset.symbol,
                f"{asset.quantity:.6f}".rstrip('0').rstrip('.'),
                f"${asset.purchase_price:.2f}",
                f"${asset.current_price:.2f}",
                f"${pl_data['current_value']:.2f}",
                f"${pl_data['profit_loss']:.2f}",
                f"{pl_data['profit_loss_percent']:.2f}%"
            ), tags=(color,))
        
        self.portfolio_tree.tag_configure("green", foreground="green")
        self.portfolio_tree.tag_configure("red", foreground="red")

    def _update_usdt_prices_display(self):
        """Update dashboard table with supported coin prices in USDT."""
        if not hasattr(self, 'usdt_price_tree'):
            return

        for item in self.usdt_price_tree.get_children():
            self.usdt_price_tree.delete(item)

        if not self.usdt_prices:
            self.usdt_prices_status_label.config(
                text="No USDT prices loaded yet. Click Refresh Prices to update."
            )
            return

        for symbol in sorted(self.usdt_prices.keys()):
            price = self.usdt_prices[symbol]
            price_text = "Unavailable" if price is None else f"{price:,.6f} USDT"
            self.usdt_price_tree.insert("", tk.END, values=(symbol, price_text))

        if self.usdt_prices_updated_at:
            updated_at = self.usdt_prices_updated_at.strftime("%Y-%m-%d %H:%M:%S")
            self.usdt_prices_status_label.config(text=f"Last updated: {updated_at}")
        else:
            self.usdt_prices_status_label.config(text="USDT prices loaded.")
    
    def _update_dashboard(self):
        """Update dashboard summary."""
        summary = self.portfolio.get_total_profit_loss()
        
        total_value = summary['total_value']
        total_invested = summary['total_invested']
        total_pl = summary['total_profit_loss']
        total_percent = summary['total_profit_loss_percent']
        
        self.total_value_label.config(text=f"${total_value:,.2f}")
        self.total_invested_label.config(text=f"${total_invested:,.2f}")
        
        pl_color = "green" if total_pl >= 0 else "red"
        self.total_pl_label.config(text=f"${total_pl:,.2f}", foreground=pl_color)
        
        percent_color = "green" if total_percent >= 0 else "red"
        self.total_percent_label.config(text=f"{total_percent:.2f}%", foreground=percent_color)
    
    def _update_analysis_display(self):
        """Update analysis displays and charts."""
        # Clear existing items
        for item in self.top_tree.get_children():
            self.top_tree.delete(item)
        for item in self.worst_tree.get_children():
            self.worst_tree.delete(item)
        for item in self.alloc_tree.get_children():
            self.alloc_tree.delete(item)
        
        # Top performers
        top_assets = self.service.find_best_performers(5)
        for asset in top_assets:
            self.top_tree.insert("", tk.END, values=(
                asset['symbol'],
                f"{asset['profit_loss_percent']:.2f}%",
                f"${asset['profit_loss']:.2f}"
            ))
        
        # Worst performers
        worst_assets = self.service.find_worst_performers(5)
        for asset in worst_assets:
            self.worst_tree.insert("", tk.END, values=(
                asset['symbol'],
                f"{asset['profit_loss_percent']:.2f}%",
                f"${asset['profit_loss']:.2f}"
            ))
        
        # Allocation
        allocation = self.service.get_allocation()
        for symbol, percent in sorted(allocation.items(), key=lambda x: x[1], reverse=True):
            self.alloc_tree.insert("", tk.END, values=(
                symbol,
                f"{percent:.2f}%"
            ))
        
        # Update charts
        self._update_charts()
    
    def _update_charts(self):
        """Generate and update matplotlib charts."""
        # Clear previous charts
        for widget in self.charts_container.winfo_children():
            widget.destroy()
        
        if not self.portfolio.get_all_assets():
            label = ttk.Label(self.charts_container, text="Portfolio is empty. Add assets to see charts.", 
                             font=("Arial", 11))
            label.pack(pady=20)
            return
        
        try:
            # Create figure with subplots
            fig = Figure(figsize=(12, 5), dpi=100)
            
            # Pie chart for allocation
            ax1 = fig.add_subplot(121)
            allocation = self.service.get_allocation()
            symbols = list(allocation.keys())
            percentages = list(allocation.values())
            
            colors = plt.cm.Set3(range(len(symbols)))
            ax1.pie(percentages, labels=symbols, autopct='%1.1f%%', 
                   colors=colors, startangle=90)
            ax1.set_title('Portfolio Allocation', fontsize=12, fontweight='bold')
            
            # Bar chart for profit/loss
            ax2 = fig.add_subplot(122)
            assets = self.portfolio.get_all_assets()
            symbols_pl = [asset.symbol for asset in assets]
            pl_values = []
            
            for asset in assets:
                pl_data = asset.calculate_profit_loss()
                pl_values.append(pl_data['profit_loss_percent'])
            
            colors_pl = ['green' if x >= 0 else 'red' for x in pl_values]
            bars = ax2.bar(symbols_pl, pl_values, color=colors_pl, alpha=0.7, edgecolor='black')
            ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
            ax2.set_ylabel('Profit/Loss %', fontweight='bold')
            ax2.set_title('Profit/Loss by Asset', fontsize=12, fontweight='bold')
            ax2.tick_params(axis='x', rotation=45)
            
            # Add value labels on bars
            for bar, value in zip(bars, pl_values):
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height,
                        f'{value:.1f}%', ha='center', va='bottom' if height >= 0 else 'top',
                        fontsize=9, fontweight='bold')
            
            fig.tight_layout()
            
            # Embed in Tkinter
            canvas = FigureCanvasTkAgg(fig, master=self.charts_container)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
        except Exception as e:
            print(f"Error generating charts: {e}")
            error_label = ttk.Label(self.charts_container, 
                                   text=f"Error generating charts: {str(e)}", 
                                   font=("Arial", 10), foreground="red")
            error_label.pack(pady=20)
    
    
    def _start_auto_update(self):
        """Start automatic price update thread."""
        def auto_update():
            while self.is_running:
                try:
                    import time
                    time.sleep(60)  # Update every 60 seconds
                    
                    if self.portfolio.get_all_assets():
                        self.service.update_all_prices()
                        self.storage.save_portfolio(self.portfolio)
                        self.root.after(0, self._update_dashboard)
                        self.root.after(0, self._update_portfolio_display)

                    self._load_usdt_prices()
                    self.root.after(0, self._update_usdt_prices_display)
                except Exception as e:
                    print(f"Auto-update error: {e}")
        
        self.update_thread = threading.Thread(target=auto_update, daemon=True)
        self.update_thread.start()
    
    def _on_closing(self):
        """Handle window closing."""
        self.is_running = False
        self.storage.save_portfolio(self.portfolio)
        self.root.destroy()
    
    def _get_supported_cryptos_text(self) -> str:
        """Get formatted list of supported cryptocurrencies."""
        cryptos = list(PriceService.get_supported_cryptos().keys())
        # Format in columns
        cols = 5
        text_lines = []
        for i in range(0, len(cryptos), cols):
            line = "  ".join(f"{sym:6}" for sym in cryptos[i:i+cols])
            text_lines.append(line)
        return "\n".join(text_lines)


def main():
    """Main application entry point."""
    root = tk.Tk()
    app = PriceTrackerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
