import numpy as np
import pandas as pd
import datetime

from datetime import datetime
from collections import defaultdict


from notify import message, send

from bk_module import *


#### global settings ####

orders_threshold = 30
init_order_size = 40

print(f'xxxx 0000 init_order_size: {init_order_size}')

config = {}

config['orders_threshold'] = orders_threshold
config['init_order_size'] = init_order_size
config['enable_trading'] = False

config['order_entry_count'] = 5
config['take_profit1_count'] = 10
config['take_profit2_count'] = 15
config['take_profit_exit'] = 20



#### run pnl
if __name__ == '__main__':

    print(f'xxxx main init_order_size: {init_order_size}')
    print(f'xxxx main config: {config}')

    today = datetime.today().date().strftime('%m%d%Y')
    today = '07162020'
    #trade_file = f'/data/alpaca_paperlive_trades_{today}.csv'
    signals_file = f'/data/signals_ui_{today}.csv'

    df = pd.read_csv(signals_file, header=None)
    df.columns = ['xx','count', 'symbol', 'qtm', 'n', 'open', 'mn', 'mu', 'md', 'mx', 'vwap', 'close', 'dv', 'atr', 'signal']
    df['sym'] = df['symbol'].apply(lambda x: str(x).split("'")[1])

    for count, g in df.groupby('count'):
        #print(f'xxxx count: {count}, signals: {len(g)}')

        signal_long = g.loc[g.signal == 'Mom_Long']
        signals_short = g.loc[g.signal == 'Mom_Short']

        # send to order event queue -
        if len(signal_long) > 0:
            update_signals_count(long_signals_count_map, long_signals_count_dict, signal_long, 1, config)
            remove_signals_count(short_signals_count_map, short_signals_count_dict, signal_long)

        if len(signals_short) > 0:
            update_signals_count(short_signals_count_map, short_signals_count_dict, signals_short, -1, config)
            remove_signals_count(long_signals_count_map, long_signals_count_dict, signals_short)


    ### print summary
    long_signals_rank = sorted(long_signals_count_dict.items(), key=lambda x: x[1], reverse=True)
    short_signals_rank = sorted(short_signals_count_dict.items(), key=lambda x: x[1], reverse=True)

    print(f'$$$$ Long: {long_signals_rank}, Short: {short_signals_rank}')
    print(datetime.now())


    orders_hist_df = pd.DataFrame(orders_hist, columns=['order_time', 'symbol', 'size', 'side', 'ord_type', 'ref_price', 'signal_time', 'order_id'])

    print('xxxx trades sample:')
    print(orders_hist_df.tail())


    pnl_df, pnl_info = get_agg_pnl(orders_hist_df)

    print('xxxx pnl_info:')
    print(pnl_df)
    print(f'config: {config}')

    email_body = pnl_df.to_html()
    email_body += '<br><hr>'
    email_body += pnl_info.to_html()
    email_body += '<br><hr>'
    email_body += f'config: {config}'

    ### send email 
    msg = message(subject=f'Daily pnl backtest report - {today}', text=email_body, img='/home/gfeng/html/logo/sp500.png', attachment=signals_file)

    send(msg)

