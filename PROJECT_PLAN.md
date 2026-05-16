# Crypto/Stock Price Tracker - Project Plan

## 1. Project Overview
A desktop application built with Tkinter that allows users to track real-time cryptocurrency and stock prices, manage a personal investment portfolio, and monitor profit/loss. The application fetches live market data from free APIs and provides a user-friendly interface for portfolio management.

## 2. Project Goals
- Enable real-time tracking of asset prices
- Allow users to manage personal investment portfolios
- Calculate and display profit/loss metrics
- Provide data persistence and export capabilities
- Create an intuitive desktop interface

## 3. Project Structure
```
finance-tracker/
├── src/
│   ├── __init__.py
│   ├── main.py                 # Entry point
│   ├── models.py               # Asset and Portfolio classes
│   ├── services.py             # API and business logic
│   ├── storage.py              # File persistence
│   ├── validators.py           # Input validation with regex
│   ├── decorators.py           # Custom decorators
│   └── gui.py                  # Tkinter GUI
├── tests/
│   ├── __init__.py
│   └── test_models.py          # Unit tests
├── data/
│   ├── portfolio.json          # User portfolio data
│   ├── exchange_rates.json     # Cached exchange rates
│   └── sample_data.json        # Sample portfolio
├── requirements.txt            # Dependencies
├── README.txt                  # Instructions
└── PROJECT_PLAN.md            # This file
```

## 4. Technical Architecture

### 4.1 Core Classes (OOP Design)
1. **Asset** - Represents a single cryptocurrency/stock
   - Attributes: symbol, quantity, purchase_price, purchase_date
   - Methods: calculate_profit_loss(), get_current_value()

2. **Portfolio** - Manages collection of assets (inherits from list-like structure)
   - Methods: add_asset(), remove_asset(), get_total_value(), get_total_profit_loss()
   - Stores multiple Asset objects

3. **PriceService** - Handles API calls for real-time data
   - Methods: fetch_crypto_price(), fetch_stock_price(), get_supported_assets()

4. **PortfolioManager** - Business logic layer
   - Methods: save_portfolio(), load_portfolio(), export_csv(), export_json()

### 4.2 Data Flow
```
GUI Input → Validators → Services → Models → Storage → Persistence
```

## 5. Course Topics Coverage

| Topic | Implementation | Location |
|-------|-----------------|----------|
| Variables & Data Types | Asset properties, portfolio data | models.py |
| Arithmetic/Comparison | Profit/loss calculation | models.py |
| Conditionals & Loops | Portfolio filtering, data validation | services.py |
| Lists, Tuples, Dicts | Portfolio collection, price data | models.py, storage.py |
| File I/O (JSON/CSV) | Portfolio persistence, export | storage.py |
| Functions | Modular business logic | services.py |
| OOP & Classes | Asset, Portfolio, Manager classes | models.py |
| Inheritance | Portfolio extends base collection | models.py |
| Modules & Packages | Project organization, imports | __init__.py files |
| Decorators | @validate_input, @error_handler | decorators.py |
| Regular Expressions | Input validation for symbols | validators.py |
| Unit Testing | Test classes and methods | tests/test_models.py |
| Exception Handling | API errors, file errors, input errors | All modules |

## 6. Key Features

### 6.1 Core Features (Mandatory)
- ✅ Real-time price fetching from free APIs (CoinGecko)
- ✅ Portfolio management (add/remove assets)
- ✅ Profit/loss calculation
- ✅ Portfolio summary dashboard
- ✅ Data persistence (JSON)
- ✅ CSV export
- ✅ Search and filter functionality
- ✅ Input validation and error handling

### 6.2 Advanced Features (Optional)
- ✅ Regular expression validation for asset symbols
- ✅ Decorator-based error handling
- ✅ Generator for pagination
- ✅ Multi-asset price alerts (simple pop-ups)
- ✅ Currency conversion (optional)
- ✅ Comprehensive unit tests

## 7. Technology Stack
- **GUI Framework**: Tkinter (built-in with Python)
- **HTTP Requests**: requests library
- **Data Persistence**: JSON format
- **API**: CoinGecko (free, no authentication)
- **Testing**: unittest (built-in)
- **Data Formats**: JSON, CSV

## 8. Error Handling Strategy
- Network errors: Graceful fallback with cached data
- File errors: User notification and data recovery
- Input validation: Regex patterns and type checking
- API errors: Automatic retry logic
- Missing data: Default values and user prompts

## 9. Advanced Python Features Used
1. **OOP with Inheritance**: Portfolio extends collection behavior
2. **Decorators**: Input validation and error handling decorators
3. **Regular Expressions**: Symbol and input format validation
4. **Generators**: For paginating large portfolios
5. **Unit Testing**: Comprehensive test suite
6. **Modules & Packages**: Organized project structure
7. **Exception Handling**: Custom exceptions and error recovery

## 10. Testing Strategy
- Unit tests for models (Asset, Portfolio)
- Integration tests for storage and API
- GUI testing through manual user interaction
- Edge case testing for calculations and validation

## 11. Deliverables
1. Complete Python source code (all .py files)
2. Portfolio data (JSON format)
3. Unit tests with test data
4. README with setup and usage instructions
5. Requirements.txt with dependencies
6. Project documentation and plan
