import os
import sys
import pandas as pd
import numpy as np

from pandas_datareader import data
import ffn
import datetime
import configparser
from datetime import datetime, timedelta
from sys import argv
import pickle

import plotly
import plotly.graph_objects as go

from flask import Flask, render_template, request, send_file, jsonify
from jinja2 import Environment, FileSystemLoader


### global variables ###
company = "AQ Analytics"
search_list = []


def load_models():
    file_name = "models/model_file.p"
    with open(file_name, 'rb') as pickled:
       data = pickle.load(pickled)
       model = data['model']
    return model


def rebase_series(series):
    return (series/series.iloc[0]) * 100


def get_yahoo_data(tickers, start_in="2020-01-01", end=datetime.now().date().strftime('%Y-%m-%d')):  
    dat = []

    for s in tickers:
        try:
            s = s.strip()
            s = s.replace(".", "-").replace("'","")
            print('xxxx loading data for: ', s)

            ohlc = data.DataReader(s, "yahoo", start_in)
            ohlc = ohlc[~ohlc.index.duplicated()]
            dat.append(ohlc['Close'].copy())
        except Exception as e:
            print('ERROR: loading data ', e)            

    print("Data loaded.")
    df = pd.concat(dat, axis=1)
    df.columns = tickers
    df.fillna(method='bfill', inplace=True)
    #df.head()

    return df


def get_indicator_plots(prices):
    #df = ffn.get(ticker, start=start)

    fig = go.Figure()
            
    for j, c in enumerate(prices.columns):
        df = prices[c]
        df_stats = df.describe()

        colors = ['lightgray', 'gray', 'lightgray', 'gray', 'lightgray', 'gray', 'lightgray', 'gray']
        rg = [['min','25%'], ['25%', '50%'], ['50%','75%'],['75%','max']]
        steps = []
        for i, r in enumerate(rg):
            steps.append({'range':[df_stats[r[0]], df_stats[r[1]]], 'color': colors[i]})
        #print(steps)
        #print(df_stats)
    
        fig.add_trace(go.Indicator(
            title = {'text':"<b>{}</b><br><span style='color: gray; font-size:0.8em'>$</span>".format(c.upper()), 'font': {"size": 12}},
            mode = "number+gauge+delta",
            value = df[-1],
            delta = {'reference': df[-2]}, # previous day
            #delta = {'reference': df_stats['mean'] - df_stats['std']*1 }, # below 1 std

            gauge = {'shape': "bullet",
                    'axis': {'range': [df_stats['min'], df_stats['max']]},
                    'bar': {'color': "black"},
                    'steps': steps,
                    'threshold': {
                        'line': {'color': "red", 'width': 2},
                        'thickness': 0.75, 
                        'value': df_stats['mean']-df_stats['std']*1
                        },             
                    },

            #domain = {'x': [0, 1], 'y': [0, 1]},
            domain = {'row': j, 'column': 0},
            ))


    #fig.update_layout(height = 200, margin = {'t':0, 'b':0, 'l':0})
    #fig.update_layout(width=400, height=200 )
    fig.update_layout(title='price indicator plots: ',
                     grid = {'rows': len(prices.columns), 'columns': 1, 'pattern': "independent"},
                     height=110*len(prices.columns),
                     )
    
    image_file = f'/tmp/AQ_indicator_{os.path.basename(config["ticker_file"]).replace(".csv",".png")}'
    print('xxxx saving image file to: ', image_file)
    
    fig.write_image(image_file)
    #plotly.io.write_image(fig=data,file="/tmp/img1.png", format="png",scale=None, width=None, height=None)

    chart = plotly.offline.plot(fig, include_plotlyjs=False, output_type='div')

    return chart



def plot_indicator_ranking(df):
    df_stats = df.describe()

    fig = go.Figure(go.Indicator(
        mode = "number+gauge+delta", value = df[-1],
        domain = {'x': [0, 1], 'y':[0, 1]},
        delta = {'reference': df[-2], 'position': "top"},
        title = {'text':f"<b>{df_stats.name.upper()}</b><br><span style='color: gray; font-size:0.8em'>{100*np.log(df[-1]/df.mean()):.2f}%</span>", 'font': {"size": 14}},
        gauge = {
            'shape': "bullet",
            'axis': {'range': [df_stats['min'], df_stats['max']]},
            'threshold': {
                'line': {'color': "red", 'width': 2},
                'thickness': 0.75, 'value': df_stats['mean']},
            'bgcolor': "white",
            'steps': [
                {'range': [df_stats['min'], df_stats['25%']], 'color': "cyan"},
                {'range': [df_stats['25%'], df_stats['50%']], 'color': "royalblue"},
                {'range': [df_stats['50%'], df_stats['75%']], 'color': "cyan"},
                {'range': [df_stats['75%'], df_stats['max']], 'color': "royalblue"}],
            'bar': {'color': "darkblue"}}))

    fig.update_layout(height = 220)
    #fig.show()
    
    return fig


def gen_indicator_plots(prices):
    #df = ffn.get(ticker, start=start)
    rb_prices = rebase_series(prices)
    prices_stats = rb_prices.describe()

    # rank by distance from mean or, -1 std
    prices_stats.loc['last'] = list(rb_prices.iloc[-1])
    prices_stats.loc['ret_from_mean'] = np.log(prices_stats.loc['last']/prices_stats.loc['mean'])
    prices_stats_sorted = prices_stats.sort_values('ret_from_mean', axis=1)

    charts = {}

    for j, c in enumerate(prices_stats_sorted.columns):
        df = prices[c]        
        fig = plot_indicator_ranking(df)

        #image_file = f'/tmp/AQ_indicator_{os.path.basename(config["ticker_file"]).replace(".csv",".png")}'
        image_file = f'/tmp/AQ_indicator_{c}.png'
        print('xxxx saving image file to: ', image_file)
        
        fig.write_image(image_file)
        #plotly.io.write_image(fig=data,file="/tmp/img1.png", format="png",scale=None, width=None, height=None)

        chart = plotly.offline.plot(fig, include_plotlyjs=False, output_type='div')

        charts[c] = chart

    return charts


# Flask app
#app = Flask(__name__)


def generate_gem_html(df, ticker_file):
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template("templates/{}".format(config['template_file']))

    print('xxxx DEBUG prices df: ',df.tail())

    prices = df.copy()
    plot_func = config['plot_func']+'(prices)'
    print('xxxx calling graph func: ', plot_func)
    graph = eval(plot_func)
    #graph = get_indicator_plots(prices)
    #print('xxxx DEBUG: graph - ', graph)

    charts = gen_indicator_plots(prices)

    html_out = template.render(        
        company=company,
        results=ticker_file,
        start_date=config['start_date'],
        
        # for display - 
        graph=graph, 
        charts=charts, # sorted by return from mean
    )
    
    return html_out


def generate_html_report(df, ticker_file):
    html = generate_gem_html(df, ticker_file)

    outputdir=config['output_dir']

    outfile = os.path.join(outputdir, 'AQ_{}_{}_{}.html'.format(
        config['plot_func'],
        ticker_file, datetime.today().date().strftime('%Y%m%d')))
    
    outfile = outfile.replace('.csv','')
    # df.to_csv(outfile.replace(".html", ".csv"))

    with open(outfile,"w") as file:
        file.write(html)
    
    print('xxxx output file saved to: ', outfile)
    
    return outfile


##################################################################
# global properties 
##################################################################

config = {}

def usage():
    print("usage: python application.py <configfile>")

# config utils 
def load_app_config(config_file):
    try:
        appconfig = configparser.ConfigParser()
        base_dir = os.path.abspath(os.path.dirname('__file__'))
        appconfig.read(os.path.join(base_dir, config_file))

        print('==================')
        for c in appconfig['DEFAULT']:
            config[c] = appconfig['DEFAULT'][c]
        print("DEFAULT configs: ", config)
        print('------------------')
    except Exception as e:
        raise Exception('Error init/start Services. %s' %e) 


def main():
    # set config file to be same as main script    
    config_file = os.path.basename(argv[0]).replace(".py", ".config")
    print('xxxx config_file: ',config_file)

    if len(sys.argv) < 2:
        usage()
        #sys.exit(-1)
        load_app_config(config_file)
    else:
        # load input configs
        load_app_config(sys.argv[1])
        
    ticker_file = config['ticker_file']
    start_in = config.get('start_date', None)

    if start_in is None:
        today = datetime.now()
        start_dt = datetime(today.year - 1, today.month, today.day)
        start_in = start_dt.strftime('%Y-%m-%d')
        config['start_date'] = start_in

    print('xxxx start_in: ', start_in)

    tickers = list(pd.read_csv(ticker_file).Symbol.unique())
    df = get_yahoo_data(tickers, start_in)

    return generate_html_report(df, os.path.basename(ticker_file))   


#### app main ####
if __name__ == '__main__':
    #app.run(debug=True, host='0.0.0.0', port=80)
    main()
