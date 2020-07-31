import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

pd.options.mode.chained_assignment = None


def load_price_history() -> pd.DataFrame:
    filename = '/home/kris/repos/trend/stooq/daily/uk/lse stocks intl/ogzd.uk.txt'
    # filename = '/home/kris/repos/trend/stooq/daily/uk/lse etfs/1/hzad.uk.txt'
    df = pd.read_csv(filename)

    df = df.loc[:, ['CLOSE']]

    df.reset_index(level=0, inplace=True)
    df.columns = ['days', 'price']

    return df


def find_smallest_zz(df: pd.DataFrame):
    aux_df = df[df.zz.notna()]
    aux_df.reset_index(level=0, inplace=True)
    for i in aux_df.index:
        if i > 2:
            p3 = aux_df.zz.iloc[i - 3]
            p2 = aux_df.zz.iloc[i - 2]
            p1 = aux_df.zz.iloc[i - 1]
            p0 = aux_df.zz.iloc[i - 0]

            # remove ascending/descending zz, leave spikes only
            if (p3 <= p2 <= p0 and p3 <= p1 <= p0) or (p3 >= p2 >= p0 and p3 >= p1 >= p0):
                aux_df.zz.iloc[i - 2] = np.nan
                aux_df.zz.iloc[i - 1] = np.nan

    df.set_index('days', inplace=True)
    aux_df.set_index('days', inplace=True)
    df.zz = aux_df.zz
    df.reset_index(level=0, inplace=True)


def simplify(df: pd.DataFrame):
    df['zz'] = pd.Series()
    df.zz.iloc[0] = df.price.iloc[0]
    df.zz.iloc[-1] = df.price.iloc[-1]

    last_turn = df.price.iloc[0]

    for i in df.index:
        if i > 0:
            prev_price = df.price.iloc[i - 1]
            price = df.price.iloc[i]

            if prev_price > price and prev_price > last_turn:
                df.zz.iloc[i - 1] = last_turn = prev_price
            if prev_price < price and prev_price < last_turn:
                df.zz.iloc[i - 1] = last_turn = prev_price

    df['zz_orig'] = df.zz
    find_smallest_zz(df)
    find_smallest_zz(df)
    find_smallest_zz(df)
    find_smallest_zz(df)


def display(df: pd.DataFrame):
    df['ma'] = df.price.rolling(window=200).mean()

    zz_df = df[df.zz.notna()]
    plt.plot(zz_df.days, zz_df.zz, label='ZZ', color='blue')

    zz_orig_df = df[df.zz_orig.notna()]
    plt.plot(zz_orig_df.days, zz_orig_df.zz_orig, label='Price', color='green')

    # zz_orig = zz_orig_df.zz_orig
    # zz_diff = abs(zz_orig - zz_orig.shift(1))
    # plt.hist(zz_diff, bins='auto', label='zz_diff')

    plt.legend(loc='upper left')
    plt.grid()
    plt.tight_layout()
    man = plt.get_current_fig_manager()
    # man.window.showMaximized()
    plt.show()


def main():
    df = load_price_history()
    simplify(df)
    display(df)


if __name__ == '__main__':
    main()
