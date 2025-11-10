import pandas as pd

class Portfolio:

    def __init__(self,
        initial_cash=1000,
        stop_loss_pct=0.02,
        profit_ratio=1.5
    ):
        self.initial_cash = initial_cash
        self.stop_loss_pct = stop_loss_pct
        self.profit_ratio = profit_ratio
        self.take_profit_pct = stop_loss_pct * profit_ratio

    def run(self, df: pd.DataFrame):
        cash = self.initial_cash
        in_trade = False
        entry_price = 0
        entry_date = None
        trades = []
        portfolio_values = []

        target_price = 0
        stop_price = 0

        for i in range(len(df)):
            price = df['Close'].iloc[i]
            date = df['date'].iloc[i]

            if not in_trade:
                if df['Buy_Signal'].iloc[i] == 1:
                    entry_price = price
                    stop_price = entry_price * (1 - self.stop_loss_pct)
                    target_price = entry_price * (1 + self.take_profit_pct)
                    entry_date = date
                    in_trade = True
                    print(f"BUY at {entry_price:.2f} on {date.date()} | Target: {target_price:.2f}, Stop: {stop_price:.2f}")
            else:
                if price >= target_price:
                    cash = cash * (target_price / entry_price)
                    print(f"SELL (TP HIT) at {target_price:.2f} on {date.date()} | Portfolio: {cash:.2f}")
                    trades.append((entry_date, date, entry_price, target_price, 'win'))
                    in_trade = False
                elif price <= stop_price:
                    cash = cash * (stop_price / entry_price)
                    print(f"SELL (STOP HIT) at {stop_price:.2f} on {date.date()} | Portfolio: {cash:.2f}")
                    trades.append((entry_date, date, entry_price, stop_price, 'loss'))
                    in_trade = False

            portfolio_values.append(cash)

        df['Portfolio'] = portfolio_values


