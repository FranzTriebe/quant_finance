import numpy as np
import numpy as py
import pandas as pd
#import pandas_datareader as pdr
import yfinance as yhf
import matplotlib.pyplot as plt

#gld = yhf.('GLD')
#gld.head()

#Gold Ticker
gold = yhf.Ticker('GLD')
#getting the full data
gold_history = gold.history(period='10y')
#adding a day column
day = np.arange(1, len(gold_history) + 1)
gold_history["day"] = day
#dropping not needed columns for momentum strategy and adjusting order of columns
gold_history.drop(columns = ['Volume', 'Dividends', 'Stock Splits', 'Capital Gains'], inplace=True)
gold_history = gold_history[['day', 'Open', 'High', 'Low', 'Close']]
#checking out the data
print(gold_history.head())
print(gold_history.columns)
print(gold_history.info())
print(gold_history.describe())