=== CRYPTO/STOCK PRICE TRACKER ===
Real-time Portfolio Management Application

SETUP & INSTALLATION
====================

1. Prerequisites
   - Python 3.8 or higher
   - pip package manager

2. Install Dependencies
   Run the following command to install required packages:
   
   pip install -r requirements.txt

3. First Run
   - Navigate to the project directory
   - Run: python src/main.py
   - The application will create necessary directories and files automatically

USAGE
=====

1. Dashboard Tab
   - View portfolio summary
   - See total value, invested amount, and profit/loss
   - Refresh prices from API

2. Portfolio Tab
   - View all your holdings
   - See current prices and profit/loss for each asset
   - Remove assets from portfolio

3. Add Asset Tab
   - Add new cryptocurrency or stock to portfolio
   - Specify quantity and purchase price
   - Current price fetches automatically from API

4. Analysis Tab
   - View top and worst performing assets
   - See portfolio allocation by percentage
   - Identify best investment opportunities

5. Settings Tab
   - Change currency (USD, EUR, GBP, etc.)
   - Rename portfolio
   - Create and manage backups
   - Export portfolio report

FEATURES
========

Real-Time Price Tracking
- Fetches live prices from CoinGecko API (free, no authentication)
- Automatic updates every 60 seconds
- Manual refresh available anytime

Portfolio Management
- Add/remove assets easily
- Track purchase price and date
- Calculate profit/loss automatically
- Combine holdings of same asset

Data Persistence
- All portfolio data saved in JSON format (data/portfolio.json)
- Automatic backups created daily
- Export to CSV for external analysis

Profit/Loss Analysis
- Per-asset profit/loss calculation
- Portfolio-wide performance metrics
- Top and worst performer identification
- Portfolio allocation percentages

Supported Assets
================

Cryptocurrencies:
BTC, ETH, BNB, XRP, ADA, SOL, DOT, DOGE, SHIB, LINK,
MATIC, AVAX, LTC, BCH, XMR, ATOM, ALGO, USDT, USDC, DAI

Stocks (symbols only, prices require API key):
AAPL, MSFT, GOOGL, AMZN, TSLA, META, NVDA, JPM, V, JNJ

IMPORTANT NOTES
===============

- API Limitations: CoinGecko has rate limits. Excessive requests may be throttled
- Price Cache: Prices are cached for 60 seconds to avoid excessive API calls
- Backups: Created automatically, stored in data/backups/ directory
- Data Format: All data saved as JSON for easy parsing and backup

TROUBLESHOOTING
===============

Issue: "requests" module not found
Solution: Run 'pip install -r requirements.txt'

Issue: API requests timing out
Solution: Check internet connection, API may be temporarily unavailable

Issue: GUI not starting
Solution: Ensure Tkinter is installed (comes with Python by default)

Issue: Portfolio data lost
Solution: Check data/backups/ for automatic backups

FILE STRUCTURE
==============

project/
├── src/                    # Source code
│   ├── main.py            # Entry point
│   ├── gui.py             # Tkinter GUI
│   ├── models.py          # Asset and Portfolio classes
│   ├── services.py        # API and business logic
│   ├── storage.py         # File persistence
│   ├── validators.py      # Input validation
│   └── decorators.py      # Reusable decorators
├── tests/                 # Unit tests
│   └── test_models.py     # Test suite
├── data/                  # User data
│   ├── portfolio.json     # Main portfolio file
│   ├── backups/          # Backup copies
│   └── exports/          # Exported CSV files
├── requirements.txt       # Dependencies
└── README.txt            # This file

COMMAND LINE USAGE
==================

Run application:
    python src/main.py

Run unit tests:
    python -m pytest tests/
    or
    python tests/test_models.py

SYSTEM REQUIREMENTS
===================

Operating System: Windows, macOS, Linux
RAM: 512 MB minimum
Disk Space: 100 MB for application and data
Network: Required for real-time price updates
Python: 3.8 or later

SUPPORT & DOCUMENTATION
=======================

For detailed project documentation, see PROJECT_PLAN.md

Report issues or feature requests through code comments.

DISCLAIMER
==========

This application is for educational and personal use only.
Do not rely solely on this tool for investment decisions.
Always verify data and conduct proper research before investing.
Past performance does not guarantee future results.

Happy investing!
