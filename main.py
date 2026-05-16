from __future__ import annotations

import csv
import json
import threading
import time
import tkinter as tk
from dataclasses import asdict, dataclass, field
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Iterable


APP_DIR = Path(__file__).resolve().parent
PORTFOLIO_FILE = APP_DIR / "portfolio.json"
UPDATE_INTERVAL_MS = 10_000


class PriceLookupError(RuntimeError):
    """Raised when the app cannot fetch a price for an asset."""


@dataclass
class Asset:
    symbol: str
    name: str
    asset_type: str
    quantity: float
    purchase_price: float
    alert_price: float | None = None
    current_price: float = 0.0
    last_updated: str = ""
    id: str = field(default_factory=lambda: str(time.time_ns()))

    @property
    def cost_basis(self) -> float:
        return self.quantity * self.purchase_price

    @property
    def market_value(self) -> float:
        return self.quantity * self.current_price

    @property
    def profit_loss(self) -> float:
        return self.market_value - self.cost_basis

    @property
    def profit_loss_percent(self) -> float:
        if self.cost_basis == 0:
            return 0.0
        return (self.profit_loss / self.cost_basis) * 100

    @classmethod
    def from_dict(cls, payload: dict) -> "Asset":
        return cls(
            id=str(payload.get("id") or time.time_ns()),
            symbol=str(payload.get("symbol", "")).strip().lower(),
            name=str(payload.get("name", "")).strip(),
            asset_type=str(payload.get("asset_type", "crypto")).strip().lower(),
            quantity=float(payload.get("quantity", 0)),
            purchase_price=float(payload.get("purchase_price", 0)),
            alert_price=(
                float(payload["alert_price"])
                if payload.get("alert_price") not in (None, "")
                else None
            ),
            current_price=float(payload.get("current_price", 0)),
            last_updated=str(payload.get("last_updated", "")),
        )


class Portfolio:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.assets: list[Asset] = []
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            self.assets = []
            return

        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            self.assets = [Asset.from_dict(item) for item in payload.get("assets", [])]
        except (json.JSONDecodeError, OSError, TypeError, ValueError) as exc:
            raise RuntimeError(f"Could not load portfolio file: {exc}") from exc

    def save(self) -> None:
        payload = {"assets": [asdict(asset) for asset in self.assets]}
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def add(self, asset: Asset) -> None:
        self.assets.append(asset)
        self.save()

    def remove(self, asset_ids: Iterable[str]) -> None:
        remove_ids = set(asset_ids)
        self.assets = [asset for asset in self.assets if asset.id not in remove_ids]
        self.save()

    def total_value(self) -> float:
        return sum(asset.market_value for asset in self.assets)

    def total_cost(self) -> float:
        return sum(asset.cost_basis for asset in self.assets)

    def total_profit_loss(self) -> float:
        return self.total_value() - self.total_cost()

    def export_csv(self, path: Path) -> None:
        columns = [
            "asset_type",
            "symbol",
            "name",
            "quantity",
            "purchase_price",
            "current_price",
            "market_value",
            "profit_loss",
            "profit_loss_percent",
            "alert_price",
            "last_updated",
        ]

        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns)
            writer.writeheader()
            for asset in self.assets:
                writer.writerow(
                    {
                        "asset_type": asset.asset_type,
                        "symbol": asset.symbol.upper(),
                        "name": asset.name,
                        "quantity": asset.quantity,
                        "purchase_price": asset.purchase_price,
                        "current_price": asset.current_price,
                        "market_value": asset.market_value,
                        "profit_loss": asset.profit_loss,
                        "profit_loss_percent": asset.profit_loss_percent,
                        "alert_price": asset.alert_price or "",
                        "last_updated": asset.last_updated,
                    }
                )

    def export_json(self, path: Path) -> None:
        payload = {"assets": [asdict(asset) for asset in self.assets]}
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


class PriceService:
    def __init__(self, timeout: int = 8) -> None:
        self.timeout = timeout
        try:
            import requests
        except ImportError as exc:
            raise RuntimeError(
                "The 'requests' package is required. Install it with "
                "'pip install -r requirements.txt'."
            ) from exc

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "TkinterPortfolioTracker/1.0",
                "Accept": "application/json",
            }
        )

    def update_prices(self, assets: Iterable[Asset]) -> None:
        grouped = {"crypto": [], "stock": []}
        for asset in assets:
            grouped.setdefault(asset.asset_type, []).append(asset)

        if grouped.get("crypto"):
            self._update_crypto_prices(grouped["crypto"])
        if grouped.get("stock"):
            self._update_stock_prices(grouped["stock"])

    def _update_crypto_prices(self, assets: list[Asset]) -> None:
        ids = ",".join(sorted({asset.symbol.lower() for asset in assets}))
        url = "https://api.coingecko.com/api/v3/simple/price"
        response = self.session.get(
            url,
            params={"ids": ids, "vs_currencies": "usd"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        prices = response.json()
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        for asset in assets:
            price = prices.get(asset.symbol.lower(), {}).get("usd")
            if price is None:
                raise PriceLookupError(
                    f"No CoinGecko USD price found for crypto ID '{asset.symbol}'."
                )
            asset.current_price = float(price)
            asset.last_updated = timestamp

    def _update_stock_prices(self, assets: list[Asset]) -> None:
        symbols = ",".join(sorted({asset.symbol.upper() for asset in assets}))
        url = "https://query1.finance.yahoo.com/v7/finance/quote"
        response = self.session.get(
            url,
            params={"symbols": symbols},
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json().get("quoteResponse", {}).get("result", [])
        prices = {
            item.get("symbol", "").upper(): item.get("regularMarketPrice")
            for item in payload
        }
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        for asset in assets:
            price = prices.get(asset.symbol.upper())
            if price is None:
                raise PriceLookupError(
                    f"No Yahoo Finance price found for stock symbol '{asset.symbol}'."
                )
            asset.current_price = float(price)
            asset.last_updated = timestamp


class PortfolioTrackerApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Crypto/Stock Price Tracker")
        self.geometry("1120x680")
        self.minsize(920, 560)

        try:
            self.portfolio = Portfolio(PORTFOLIO_FILE)
        except RuntimeError as exc:
            messagebox.showerror("Portfolio Error", str(exc))
            self.portfolio = Portfolio(APP_DIR / "portfolio.recovered.json")

        try:
            self.price_service: PriceService | None = PriceService()
        except RuntimeError as exc:
            self.price_service = None
            messagebox.showwarning("Missing Dependency", str(exc))
        self.asset_ids_by_row: dict[str, str] = {}
        self.alerted_assets: set[str] = set()
        self.refresh_running = False

        self._configure_style()
        self._build_ui()
        self._render_portfolio()
        self.after(300, self.refresh_prices)
        self.after(UPDATE_INTERVAL_MS, self._scheduled_refresh)

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview", rowheight=28)
        style.configure("Summary.TLabel", font=("Segoe UI", 12, "bold"))
        style.configure("Positive.TLabel", foreground="#177245")
        style.configure("Negative.TLabel", foreground="#B42318")

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        form = ttk.LabelFrame(self, text="Add Asset", padding=12)
        form.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))
        for column in range(9):
            form.columnconfigure(column, weight=1)

        self.asset_type = tk.StringVar(value="crypto")
        self.symbol = tk.StringVar()
        self.name = tk.StringVar()
        self.quantity = tk.StringVar()
        self.purchase_price = tk.StringVar()
        self.alert_price = tk.StringVar()
        self.search_text = tk.StringVar()

        self._field(form, "Type", 0, ttk.Combobox(
            form,
            textvariable=self.asset_type,
            values=("crypto", "stock"),
            state="readonly",
            width=10,
        ))
        self._field(form, "Symbol/ID", 1, ttk.Entry(form, textvariable=self.symbol, width=16))
        self._field(form, "Name", 2, ttk.Entry(form, textvariable=self.name, width=18))
        self._field(form, "Quantity", 3, ttk.Entry(form, textvariable=self.quantity, width=14))
        self._field(
            form,
            "Purchase $",
            4,
            ttk.Entry(form, textvariable=self.purchase_price, width=14),
        )
        self._field(
            form,
            "Alert $",
            5,
            ttk.Entry(form, textvariable=self.alert_price, width=14),
        )

        ttk.Button(form, text="Add", command=self.add_asset).grid(
            row=1, column=6, sticky="ew", padx=(8, 0)
        )
        ttk.Button(form, text="Refresh", command=self.refresh_prices).grid(
            row=1, column=7, sticky="ew", padx=(8, 0)
        )
        ttk.Button(form, text="Remove", command=self.remove_selected).grid(
            row=1, column=8, sticky="ew", padx=(8, 0)
        )

        body = ttk.Frame(self, padding=(12, 6))
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(0, weight=1)
        body.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(body)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        toolbar.columnconfigure(1, weight=1)

        ttk.Label(toolbar, text="Search").grid(row=0, column=0, sticky="w")
        search_entry = ttk.Entry(toolbar, textvariable=self.search_text)
        search_entry.grid(row=0, column=1, sticky="ew", padx=(8, 12))
        self.search_text.trace_add("write", lambda *_: self._render_portfolio())

        ttk.Button(toolbar, text="Export CSV", command=self.export_csv).grid(
            row=0, column=2, padx=(0, 8)
        )
        ttk.Button(toolbar, text="Export JSON", command=self.export_json).grid(
            row=0, column=3
        )

        columns = (
            "type",
            "symbol",
            "name",
            "quantity",
            "purchase",
            "current",
            "value",
            "pl",
            "pl_pct",
            "alert",
            "updated",
        )
        self.tree = ttk.Treeview(body, columns=columns, show="headings", selectmode="extended")
        headings = {
            "type": "Type",
            "symbol": "Symbol/ID",
            "name": "Name",
            "quantity": "Qty",
            "purchase": "Purchase $",
            "current": "Current $",
            "value": "Value",
            "pl": "P/L",
            "pl_pct": "P/L %",
            "alert": "Alert $",
            "updated": "Updated",
        }
        widths = {
            "type": 80,
            "symbol": 110,
            "name": 160,
            "quantity": 90,
            "purchase": 100,
            "current": 100,
            "value": 110,
            "pl": 110,
            "pl_pct": 90,
            "alert": 90,
            "updated": 150,
        }
        for column, heading in headings.items():
            self.tree.heading(column, text=heading)
            self.tree.column(column, width=widths[column], anchor="e")
        self.tree.column("type", anchor="center")
        self.tree.column("symbol", anchor="w")
        self.tree.column("name", anchor="w")
        self.tree.grid(row=1, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(body, command=self.tree.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.tag_configure("profit", foreground="#177245")
        self.tree.tag_configure("loss", foreground="#B42318")

        summary = ttk.Frame(self, padding=12)
        summary.grid(row=2, column=0, sticky="ew")
        summary.columnconfigure((0, 1, 2, 3), weight=1)

        self.status_text = tk.StringVar(value="Ready")
        self.total_cost_text = tk.StringVar(value="Cost: $0.00")
        self.total_value_text = tk.StringVar(value="Value: $0.00")
        self.total_pl_text = tk.StringVar(value="P/L: $0.00 (0.00%)")

        ttk.Label(summary, textvariable=self.total_cost_text, style="Summary.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(summary, textvariable=self.total_value_text, style="Summary.TLabel").grid(
            row=0, column=1, sticky="w"
        )
        self.total_pl_label = ttk.Label(
            summary, textvariable=self.total_pl_text, style="Summary.TLabel"
        )
        self.total_pl_label.grid(row=0, column=2, sticky="w")
        ttk.Label(summary, textvariable=self.status_text).grid(row=0, column=3, sticky="e")

    def _field(self, parent: ttk.Frame, label: str, column: int, widget: ttk.Widget) -> None:
        ttk.Label(parent, text=label).grid(row=0, column=column, sticky="w", padx=(0, 8))
        widget.grid(row=1, column=column, sticky="ew", padx=(0, 8))

    def add_asset(self) -> None:
        try:
            asset = self._asset_from_form()
        except ValueError as exc:
            messagebox.showwarning("Invalid Asset", str(exc))
            return

        self.portfolio.add(asset)
        self._clear_form()
        self._render_portfolio()
        self.refresh_prices()

    def _asset_from_form(self) -> Asset:
        symbol = self.symbol.get().strip()
        name = self.name.get().strip() or symbol.upper()
        asset_type = self.asset_type.get().strip().lower()

        if asset_type not in {"crypto", "stock"}:
            raise ValueError("Choose either crypto or stock.")
        if not symbol:
            raise ValueError("Enter a CoinGecko crypto ID or stock symbol.")

        try:
            quantity = float(self.quantity.get())
            purchase_price = float(self.purchase_price.get())
            alert_price = (
                float(self.alert_price.get())
                if self.alert_price.get().strip()
                else None
            )
        except ValueError as exc:
            raise ValueError("Quantity, purchase price, and alert must be numbers.") from exc

        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")
        if purchase_price < 0:
            raise ValueError("Purchase price cannot be negative.")
        if alert_price is not None and alert_price <= 0:
            raise ValueError("Alert price must be greater than zero.")

        normalized_symbol = symbol.lower() if asset_type == "crypto" else symbol.upper()
        return Asset(
            symbol=normalized_symbol,
            name=name,
            asset_type=asset_type,
            quantity=quantity,
            purchase_price=purchase_price,
            alert_price=alert_price,
        )

    def _clear_form(self) -> None:
        self.symbol.set("")
        self.name.set("")
        self.quantity.set("")
        self.purchase_price.set("")
        self.alert_price.set("")

    def remove_selected(self) -> None:
        selected_ids = [self.asset_ids_by_row[item] for item in self.tree.selection()]
        if not selected_ids:
            messagebox.showinfo("Remove Asset", "Select one or more assets to remove.")
            return
        if not messagebox.askyesno("Remove Asset", "Remove selected asset(s)?"):
            return
        self.portfolio.remove(selected_ids)
        self._render_portfolio()

    def refresh_prices(self) -> None:
        if self.price_service is None:
            self.status_text.set("Install requests to enable live price updates.")
            return
        if self.refresh_running or not self.portfolio.assets:
            return

        self.refresh_running = True
        self.status_text.set("Refreshing prices...")
        worker = threading.Thread(target=self._refresh_prices_worker, daemon=True)
        worker.start()

    def _refresh_prices_worker(self) -> None:
        try:
            self.price_service.update_prices(self.portfolio.assets)
            self.portfolio.save()
        except Exception as exc:
            self.after(0, lambda: self._finish_refresh(str(exc)))
            return
        self.after(0, lambda: self._finish_refresh(None))

    def _finish_refresh(self, error: str | None) -> None:
        self.refresh_running = False
        if error:
            self.status_text.set(f"Price update failed: {error}")
        else:
            self.status_text.set("Prices updated")
            self._check_alerts()
        self._render_portfolio()

    def _scheduled_refresh(self) -> None:
        self.refresh_prices()
        self.after(UPDATE_INTERVAL_MS, self._scheduled_refresh)

    def _check_alerts(self) -> None:
        for asset in self.portfolio.assets:
            if asset.alert_price is None or asset.id in self.alerted_assets:
                continue
            if asset.current_price >= asset.alert_price:
                self.alerted_assets.add(asset.id)
                messagebox.showinfo(
                    "Price Alert",
                    f"{asset.name} ({asset.symbol.upper()}) reached "
                    f"${asset.current_price:,.2f}.",
                )

    def _render_portfolio(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.asset_ids_by_row.clear()

        search = self.search_text.get().strip().lower()
        for asset in self.portfolio.assets:
            haystack = f"{asset.asset_type} {asset.symbol} {asset.name}".lower()
            if search and search not in haystack:
                continue

            tag = "profit" if asset.profit_loss >= 0 else "loss"
            values = (
                asset.asset_type.title(),
                asset.symbol.upper(),
                asset.name,
                f"{asset.quantity:g}",
                f"${asset.purchase_price:,.2f}",
                self._format_price(asset.current_price),
                f"${asset.market_value:,.2f}",
                f"${asset.profit_loss:,.2f}",
                f"{asset.profit_loss_percent:,.2f}%",
                self._format_price(asset.alert_price),
                asset.last_updated or "Never",
            )
            row_id = self.tree.insert("", "end", values=values, tags=(tag,))
            self.asset_ids_by_row[row_id] = asset.id

        total_cost = self.portfolio.total_cost()
        total_value = self.portfolio.total_value()
        total_pl = self.portfolio.total_profit_loss()
        total_pl_percent = (total_pl / total_cost * 100) if total_cost else 0

        self.total_cost_text.set(f"Cost: ${total_cost:,.2f}")
        self.total_value_text.set(f"Value: ${total_value:,.2f}")
        self.total_pl_text.set(f"P/L: ${total_pl:,.2f} ({total_pl_percent:,.2f}%)")
        self.total_pl_label.configure(
            style="Positive.TLabel" if total_pl >= 0 else "Negative.TLabel"
        )

    def _format_price(self, value: float | None) -> str:
        if value is None:
            return ""
        if value == 0:
            return "$0.00"
        if abs(value) < 0.01:
            return f"${value:,.8f}"
        return f"${value:,.2f}"

    def export_csv(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Export CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
        )
        if not path:
            return
        try:
            self.portfolio.export_csv(Path(path))
        except OSError as exc:
            messagebox.showerror("Export Failed", str(exc))
            return
        messagebox.showinfo("Export Complete", f"Portfolio exported to {path}.")

    def export_json(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Export JSON",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
        )
        if not path:
            return
        try:
            self.portfolio.export_json(Path(path))
        except OSError as exc:
            messagebox.showerror("Export Failed", str(exc))
            return
        messagebox.showinfo("Export Complete", f"Portfolio exported to {path}.")


def main() -> None:
    app = PortfolioTrackerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
