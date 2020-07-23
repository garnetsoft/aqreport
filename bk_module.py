
### backtet module - using signals_ui.csv data from live trading

"""
orders_threshold = 101
init_order_size = 4

print(f'xxxx init_order_size: {init_order_size}')

config = {}
config['orders_threshold'] = 101
config['init_order_size'] = 4
config['enable_trading'] = False
"""


import numpy as np
import pandas as pd
import datetime
from datetime import datetime
from collections import defaultdict

def gen_order_id():
    return datetime.now()


def send_entry_order2(sym, size, side, signal, entry_type):
    print(f'EEEE sending {entry_type} order for signal: {sym}')

    ## - add to order_hist
    #order_id = gen_order_id()
    order_id = f"{sym}_{signal['count']}_{entry_type}"
    order_id_dict[sym] = order_id
    orders_hist.append([datetime.now(), sym, size, side, entry_type, signal['close'], signal['qtm'], order_id])
    pos[sym] = signal

    return None


def send_exit_order2(sym, size, side, signal, exit_type):
    print(f'EEEE sending {exit_type} order for signal: {sym}')

    ## - add to order_hist
    org_order_id = order_id_dict.get(sym, None)
    orders_hist.append([datetime.now(), sym, size, side, exit_type, signal['close'], signal['qtm'], org_order_id])
    #pos[sym] = signal

    return None


# track existing position size for each sym -
def get_position_size(sym):
    orders_hist_df = pd.DataFrame(orders_hist, columns=['order_time', 'symbol', 'size', 'side', 'ord_type', 'ref_price', 'signal_time', 'order_id'])
    existing_pos = orders_hist_df.loc[orders_hist_df.symbol == sym]
    #print(existing_pos)

    qty = 0.0
    for _, h in existing_pos.iterrows():
        if h['side'] == 'sell':
            qty += (-1.0*h['size'])
        elif h['side'] == 'buy':
            qty += h['size']
        else:
            print(f'ERROR: unknown order type: {h}')

    return qty



### global signal map - so it doesn't get overwritten when browser refreshes ###
## IMPL
long_signals_count_dict = defaultdict(int)
long_signals_count_map = {}
short_signals_count_dict = defaultdict(int)
short_signals_count_map = {}

# track all signals that result into orders -
orders_hist = []
orders_hist_df = pd.DataFrame()

# track every position's pnl
acct_pnl = {}
pos = {}
order_id_dict = {}


def update_signals_count(signals_count_map, signals_count_dict, signals_df, long_or_short, config):
    #### update signals_rank -- $$$ IMPL

    orders_threshold = int(config['orders_threshold'])
    init_order_size = int(config['init_order_size'])

    ORDER_ENTRY_COUNT = int(config['order_entry_count'])
    TAKE_PROFIT1_COUNT = int(config['take_profit1_count'])
    TAKE_PROFIT2_COUNT = int(config['take_profit2_count'])
    TAKE_PROFIT_EXIT = int(config['take_profit_exit'])


    for _, row in signals_df.iterrows():
        sym = row['sym']
        if isinstance(sym, bytes):
            sym = sym.decode('utf-8')

        if signals_count_dict[sym] == 0:
            signals_count_dict[sym] += 1
            signals_count_map[sym] = row
        else:
            prev = signals_count_map[sym]

            #if (prev['qtm'] != row['qtm']) and (prev['close'] != row['close']):
            if prev['qtm'] != row['qtm']:
                signals_count_dict[sym] += 1
                signals_count_map[sym] = row  # update to the latest signal details -


                #if signals_count_dict[sym] == 5:  # only sent entry order once
                if signals_count_dict[sym] == ORDER_ENTRY_COUNT:  # only sent entry order once

                    #if len(orders_hist) > int(config['orders_threshold']):
                    if len(pos) >= int(config['orders_threshold']):
                        print(f'KKKK daily orders_threshold reached, not sending order for {long_or_short} signal: {sym}')

                        ### maybe we should clear out the positions with 1/4 pct of size left to give rooms to new opportunities ??
                        # clear_residual_positions()

                    elif pos.get(sym, None) is not None:
                        print(f'FFFF already has position for signal: {sym}')

                    elif long_or_short > 0:
                        send_entry_order2(sym, init_order_size, 'buy', row, 'ENTRY_LONG')
                        #pos[sym] = row
                        #orders_hist.append(row.to_dict('records'))
                        #orders_hist.append([datetime.now(), sym, init_order_size, 'buy', 'ENTRY_LONG', row['close'], row['qtm']])

                    elif long_or_short < 0:
                        send_entry_order2(sym, init_order_size, 'sell', row, 'ENTRY_SHORT')
                        #pos[sym] = row
                        #orders_hist.append([datetime.now(), sym, init_order_size, 'sell', 'ENTRY_SHORT', row['close'], row['qtm']])

                    else:
                        print(f'XXXX Unkown state, skip {long_or_short} signal: {row}')


                # exit for profit
                elif signals_count_dict[sym] >= TAKE_PROFIT1_COUNT:
                    #if not config.get('enable_trading', False) == 'True':
                    #    print('XXXX trading is NOT enabled, ignoring {long_or_short} signal for {sym}')
                    #    pass
                    #elif pos.get(sym, None) is None:
                    if pos.get(sym, None) is None:
                        pass
                    else:
                        side = 'buy' if long_or_short < 0 else 'sell'

                        #if signals_count_dict[sym] == 10:
                        if signals_count_dict[sym] == TAKE_PROFIT1_COUNT:
                            # taking profit on existing order - do 1/2, 1/4, 1/4 method?
                            # get position size from entry order AND broker to ensure double confirmation
                            send_exit_order2(sym, init_order_size/2, side, row, 'TAKE_PROFIT_1')
                            print('$$$$ exiting 1/2 profitable position0: sell {init_order_size/2} {sym}')
                            #orders_hist.append([datetime.now(), sym, init_order_size/2, side, 'TAKE_PROFIT1', row['close'], row['qtm']])

                        #elif signals_count_dict[sym] == 15:
                        elif signals_count_dict[sym] == TAKE_PROFIT2_COUNT:
                            # taking profit on existing order - do 1/2, 1/4, 1/4 method?
                            send_exit_order2(sym, init_order_size/4, side, row, 'TAKE_PROFIT_2')
                            print('$$$$ exiting 1/4 profitable position1: sell {init_order_size/4} {sym}')
                            #orders_hist.append([datetime.now(), sym, init_order_size/4, side, 'TAKE_PROFIT2', row['close'], row['qtm']])

                        #elif signals_count_dict[sym] == 20:
                        elif signals_count_dict[sym] == TAKE_PROFIT_EXIT:
                            # taking profit on existing order - do 1/2, 1/4, 1/4 method?
                            send_exit_order2(sym, init_order_size/4, side, row, 'TAKE_PROFIT_EXIT')
                            print('$$$$ exiting 1/4 profitable position2: sell {init_order_size/4} {sym}')
                            #orders_hist.append([datetime.now(), sym, init_order_size/4, side, 'TAKE_PROFIT3', row['close'], row['qtm']])

                            del order_id_dict[sym]
                            del pos[sym]

                            ## start over - reset cache so we can trade this again if momentum builds up
                            removed = signals_count_map.pop(sym, None)
                            if removed is not None:
                                signals_count_dict.pop(sym)
                                print(f'AAAA removed signal {sym} from cache so it can be traded again $$$.')


    print(f'$$$$: {long_or_short} signals_count_dict: {signals_count_dict}')


def remove_signals_count(signals_count_map, signals_count_dict, signals_df):
    #### remove signal from opposite map if trend reverse -- $$$$ IMPL
    # exit_at_loss  - for long positions, going down to low of the day
    #               - for short positions, going up to high of the day

    for _, row in signals_df.iterrows():
        sym = row['sym']
        if isinstance(sym, bytes):
            sym = sym.decode('utf-8')

        removed = signals_count_map.pop(sym, None)
        if removed is not None:
            signals_count_dict.pop(sym)
            print(f'XXXX removed sig {sym} from opposite signals map.')

            ### NEED TO EXIT ACTIVE POSTION COMPLETELY so it can trade on opposite trend $$$
            if pos.pop(sym, None) is not None:
                print(f'$$$$ sending STOP_LOSS (exit) order for signal: {sym}')

                existing_size = get_position_size(sym)
                side = 'sell'
                if existing_size < 0:
                    side = 'buy'

                send_exit_order2(sym, abs(existing_size), side, row, 'STOP_LOSS_EXIT')

    return None


def create_long_short_signals(stats):
    # ONLY DOW 30 NAMES -


    # APPLY signals and send orders to Alpaca, update real-time postions
    signal_long = stats.loc[(stats.n>=stats_threshold) & (stats.close>=stats.mx) & (stats.close>stats.open)].copy()
    signal_long['signal'] = 'Mom_Long'

    # send to order event queue -
    if len(signal_long) > 0:
        print('$$$$ got mom LONG signals: (send to Alexa) ')
        #print(signal_long)
        # check if any active positions -
        update_signals_count(long_signals_count_map, long_signals_count_dict, signal_long, 1)
        remove_signals_count(short_signals_count_map, short_signals_count_dict, signal_long)


    signals_short = stats.loc[(stats.n>=stats_threshold) & (stats.close<=stats.mn) & (stats.close<stats.open)].copy()
    signals_short['signal'] = 'Mom_Short'

    if len(signals_short) > 0:
        print('$$$$ got SHORT signals: (send to Alexa) ')
        #print(signals_short)
        update_signals_count(short_signals_count_map, short_signals_count_dict, signals_short, -1)
        remove_signals_count(long_signals_count_map, long_signals_count_dict, signals_short)


    ## print any live pos -
    print(f'$$$$ create_long_short_signals, position count: {len(pos)}, active positions: {pos.keys()}')

    # merge Long/Short signals -
    #signals_df = pd.concat([signal_long, signals_short])
    return pd.concat([signal_long, signals_short])



### pnl func

def calc_pnl(g, long_or_short):
    entry_price = g.iloc[0]['ref_price']
    total_pnl = 0.0

    for i, (index, r) in enumerate(g.iterrows()):
        # print(f'xxxx: {i}, {r}')
        # if not r['ord_type'].startswith('ENTRY'): # calc each pnl
        if i > 0:
            exit_price = r['ref_price']
            size = r['size']
            total_pnl += (exit_price - entry_price) * size * long_or_short

    # print(f'$$$$ total_pnl: {total_pnl}, {size}')
    return total_pnl


def get_agg_pnl(df):
    long_pnl, short_pnl = 0.0, 0.0
    pnl_map = defaultdict(float)

    #for name, g in df.loc[df.symbol=='TWTR'].groupby('order_id'):
    for name, g in df.groupby('order_id'):
        #print(f'xxxx order_id {name}, DDDD: {len(g)}, {g}')
        sym = g.iloc[0]['symbol']

        if g.iloc[0]['ord_type'] == 'ENTRY_LONG':
            pnl = calc_pnl(g, 1)
            long_pnl += pnl
            pnl_map[sym] += pnl
            #print(f"xxxx LONG order_id: {name}, {g.iloc[0]['symbol']} pnl {pnl}")
        elif g.iloc[0]['ord_type'] == 'ENTRY_SHORT':
            pnl = calc_pnl(g, -1)
            short_pnl += pnl
            pnl_map[sym] += pnl
            #print(f"xxxx SHORT order_id: {name}, {g.iloc[0]['symbol']} pnl {pnl}")
        else:
            print(f'ERROR: Unknown entry order: {name}, {g}')

    print(f"$$$$ 2222 total_pnl: {long_pnl+short_pnl}, long_pnl: {long_pnl}, short_pnl: {short_pnl}, shared_traded: {np.sum(df['size'])}")
    #print(sorted(pnl_map.items(), key=lambda x: x[1], reverse=True))

    #pnl_df = pd.DataFrame([[df.iloc[0]['order_time'][:10], long_pnl+short_pnl, long_pnl, short_pnl, np.sum(df['size'])]])
    pnl_df = pd.DataFrame([[df.iloc[0]['order_time'], long_pnl+short_pnl, long_pnl, short_pnl, np.sum(df['size'])]])
    pnl_df.columns = ['date', 'todal_pnl', 'long_pnl', 'short_pnl', 'shared_traded']

    pnl_info = pd.DataFrame.from_dict(sorted(pnl_map.items(), key=lambda x: x[1], reverse=True))
    pnl_info.columns = ['sym', 'pnl']

    print(f'xxxx check return: {pnl_df}, {pnl_info}')

    return pnl_df, pnl_info


