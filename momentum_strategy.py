import numpy as np
import numpy as py
import pandas as pd
#import pandas_datareader as pdr
import yfinance as yhf
import matplotlib.pyplot as plt

#DATA PREP

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
print(gold_history.columns)
print(gold_history.info())
print(gold_history.describe())

#SIGNALS

#fast moving avg (shift since we do not know the closing on the same day)
#if we knew the closing of the 21 day the system would perform way better (see plot)
gold_history['9-day'] = gold_history['Close'].rolling(9).mean().shift()
#gold_history['9-day'] = gold_history['Close'].rolling(9).mean()
#slow moving avg
gold_history['21-day'] = gold_history['Close'].rolling(21).mean().shift()
#gold_history['21-day'] = gold_history['Close'].rolling(21).mean()
#lagging the avg
print(gold_history[20:25])
#interpreting signals
#long
gold_history['signal'] = np.where(gold_history['9-day'] > gold_history['21-day'], 1, 0)
#short
gold_history['signal'] = np.where(gold_history['9-day'] < gold_history['21-day'], -1, gold_history['signal'])
#dropping the days before 22 because no 21 day average possible
gold_history.dropna(inplace = True)
print(gold_history.head())

#RESULTS

#calculating returns
gold_history['return'] = np.log(gold_history['Close']).diff()
gold_history['system_return'] = gold_history['signal'] * gold_history['return']
gold_history['entry'] = gold_history.signal.diff()
print(gold_history.head())

#visualizing startegy for 1 year (approx 252 trading days)
plt.rcParams['figure.figsize'] = 12,6
plt.grid(True, alpha = 0.3)
plt.plot(gold_history.iloc[-252:]['Close'], label = 'GLD')
plt.plot(gold_history.iloc[-252:]['9-day'], label = '9-day')
plt.plot(gold_history.iloc[-252:]['21-day'], label = '21-day')
plt.plot(gold_history[-252:].loc[gold_history.entry == 2].index, gold_history[-252:]['9-day'][gold_history.entry == 2], '^', color = 'g', markersize = 12)
plt.plot(gold_history[-252:].loc[gold_history.entry == -2].index, gold_history[-252:]['21-day'][gold_history.entry == -2], 'v', color = 'r', markersize = 12)
plt.legend(loc = 2)
plt.show()

#STRATEGY VS LONG HOLD

#buy and hold strategy
plt.plot(np.exp(gold_history['return']).cumprod(), label = 'Buy & Hold')
#system return
plt.plot(np.exp(gold_history['system_return']).cumprod(), label = 'System')
#visualize
plt.grid(True, alpha = 0.3)
plt.legend(loc = 2)
plt.show()
#in numbers
print("Buy & Hold = ", np.exp(gold_history['return']).cumprod().iloc[-1] - 1)
print("System = ", np.exp(gold_history['system_return']).cumprod().iloc[-1] - 1)




