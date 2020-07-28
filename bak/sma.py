import matplotlib.pyplot as plt
import pandas as pd


def load_price_history() -> pd.DataFrame:
    # filename = '/home/kris/repos/trend/stooq/daily/uk/lse stocks intl/ogzd.uk.txt'
    filename = '/home/kris/repos/trend/stooq/daily/uk/lse etfs/1/hzad.uk.txt'
    df = pd.read_csv(filename)

    # df = df.loc[1420:1525, ['CLOSE']]
    # df = df.loc[1420:1625, ['CLOSE']]
    df = df.loc[:, ['CLOSE']]

    df.reset_index(level=0, inplace=True)
    df.columns = ['days', 'price']

    df['ema_fast'] = df.price.ewm(span=12, adjust=False).mean()
    df['ema_slow'] = df.price.ewm(span=26, adjust=False).mean()
    df['ema_diff'] = df.ema_fast - df.ema_slow
    df['ema_signal'] = df.ema_diff.ewm(span=9, adjust=False).mean()

    return df


SIGNAL_NIL = 0
SIGNAL_BUY = 1
SIGNAL_SELL = 2


def detect_signal(i: int, df: pd.DataFrame) -> int:
    if i == 0:
        return SIGNAL_NIL
    prev = df.ema_signal.iloc[i - 1]
    curr = df.ema_signal.iloc[i]
    if curr > 0 and prev < 0:
        return SIGNAL_BUY
    elif curr < 0 and prev > 0:
        return SIGNAL_SELL
    else:
        return SIGNAL_NIL


class Account:
    stock: int  # + long, - short
    price: float
    deposit: float
    fee = 0.02

    def __init__(self):
        self.stock = 0
        self.price = 0
        self.deposit = 0

    def open_position(self, stock: int, price: float):
        self.stock += stock
        self.price = price

    def close_position(self, price: float):
        if self.stock:
            self.deposit += self.stock * (price - self.price)
            self.deposit -= abs(self.stock) * self.fee
            self.stock = 0
            self.price = 0

    def stop_loss(self, price: float):
        loss = self.stock * (self.price - price)
        loss_ratio = loss / self.price
        if loss_ratio > 0.03:
            self.close_position(price)


def trade(df: pd.DataFrame):
    df['profit'] = 0.0
    account = Account()
    for i in df.index:
        price = df.price.iloc[i]
        signal_type = detect_signal(i, df)
        if signal_type == SIGNAL_BUY:
            assert account.stock <= 0
            account.close_position(price)
            account.open_position(1, price)
        elif signal_type == SIGNAL_SELL:
            assert account.stock >= 0
            account.close_position(price)
            account.open_position(-1, price)
        else:
            account.stop_loss(price)
        if i == df.index[-1]:
            account.close_position(df.price.iloc[-1])
        df.loc[i, 'deposit'] = account.deposit

    print(f'deposit: {account.deposit}')


def display(df: pd.DataFrame):
    plt.plot(df.days, df.price, label='OGZD', color='GREY')
    plt.plot(df.days, df.ema_fast, label='EMA FAST', color='GREEN')
    plt.plot(df.days, df.ema_slow, label='EMA SLOW', color='RED')
    plt.plot(df.days, df.ema_signal, label='EMA SIGNAL', color='BLACK')
    plt.plot(df.days, df.deposit, label='PROFIT', color='BLUE')
    plt.legend(loc='upper left')
    plt.grid()
    plt.tight_layout()
    plt.show()


def main():
    df = load_price_history()
    trade(df)
    display(df)


if __name__ == '__main__':
    main()
