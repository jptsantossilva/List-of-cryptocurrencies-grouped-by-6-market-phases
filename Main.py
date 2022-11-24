# %%
# %%
import os
from binance.client import Client
import requests
import pandas as pd
from datetime import datetime
from datetime import date
from datetime import timedelta
import numpy as np
import sys
import timeit

# %%
# %%

# calculate program run time
start = timeit.default_timer() 

# Binance
api_key = os.environ.get('binance_api')
api_secret = os.environ.get('binance_secret')

# Binance Client
client = Client(api_key, api_secret)

# Check the program has been called with the timeframe
# total arguments
n = len(sys.argv)
# print("Total arguments passed:", n)
if n < 2:
    print("Argument is missing")
    timeframe = input('Enter timeframe (1d, 8h, 4h):')
    stablecoin = input('Enter stablecoin (USDT, BUSD):')
else:
    # argv[0] in Python is always the name of the script.
    timeframe = sys.argv[1]
    stablecoin = sys.argv[2]

if timeframe == "1d": startdate = "200 day ago UTC"
elif timeframe == "8h": startdate = str(8*200)+" hour ago UTC"
elif timeframe == "4h": startdate = str(4*200)+" hour ago UTC"

# %%
tickers = client.get_ticker()
dfTickers = pd.DataFrame(tickers)
dfTickers

# %%
exchange_info = client.get_exchange_info()
coinPairs = set()

for s in exchange_info['symbols']:
    if (s['symbol'].endswith(stablecoin)
        and not(s['symbol'].endswith('DOWN'+stablecoin))
        and not(s['symbol'].endswith('UP'+stablecoin))
        and not(s['symbol'].startswith('BUSD'))
        and s['status'] == 'TRADING'):
            coinPairs.add(s['symbol'])
# print(usdt)
coinPairs = sorted(coinPairs)
print(str(len(coinPairs))+" coins found")

# %%
# exchange_info['symbols']

# %%
def SMA(values, n):
    """Simple moving average"""
    return pd.Series(values).rolling(n).mean()

# %%
def applytechnicals(df):
        df['50DSMA'] = df['Close'].rolling(50).mean()
        df['200DSMA'] = df['Close'].rolling(200).mean()

# %%
def getdata(Symbol):
    frame = pd.DataFrame(client.get_historical_klines(Symbol,
                                                      timeframe,                                        
                                                      startdate))
    
    frame = frame.iloc[:,[0,4,6]] # columns selection
    frame.columns = ['Time','Close','Volume'] #rename columns
    frame[['Close','Volume']] = frame[['Close','Volume']].astype(float) #cast to float
    # frame.Time = pd.to_datetime(frame.Time, unit='ms') #make human readable timestamp
    frame['Coinpair'] = Symbol
    frame.index = [datetime.fromtimestamp(x/1000.0) for x in frame.Time]
    
    frame = frame[['Coinpair','Close','Volume']]
    return frame

# %%
dfResult = pd.DataFrame()
# i = 0

for coinPair in coinPairs:
    # if coinPair == "VGXUSDT":
    #     print(dfResult)
    #     break    
    
    # i = i+1
    # if i == 20:
    #     break

    print("calculating "+coinPair)
    # df = pd.DataFrame()
    # print(len(df.index))
    df = getdata(coinPair)
    applytechnicals(df)
    df.dropna(inplace=True)

    if dfResult.empty:
        dfResult = df
    else:
        dfResult = pd.concat([dfResult, df])


# print(dfResult)


# %%
conditions = [
    (dfResult['Close'] > dfResult['50DSMA']) & (dfResult['Close'] < dfResult['200DSMA']) & (dfResult['50DSMA'] < dfResult['200DSMA']), # recovery phase
    (dfResult['Close'] > dfResult['50DSMA']) & (dfResult['Close'] > dfResult['200DSMA']) & (dfResult['50DSMA'] < dfResult['200DSMA']), # accumulation phase
    (dfResult['Close'] > dfResult['50DSMA']) & (dfResult['Close'] > dfResult['200DSMA']) & (dfResult['50DSMA'] > dfResult['200DSMA']), # bullish phase
    (dfResult['Close'] < dfResult['50DSMA']) & (dfResult['Close'] > dfResult['200DSMA']) & (dfResult['50DSMA'] > dfResult['200DSMA']), # warning phase
    (dfResult['Close'] < dfResult['50DSMA']) & (dfResult['Close'] < dfResult['200DSMA']) & (dfResult['50DSMA'] > dfResult['200DSMA']), # distribution phase
    (dfResult['Close'] < dfResult['50DSMA']) & (dfResult['Close'] < dfResult['200DSMA']) & (dfResult['50DSMA'] < dfResult['200DSMA'])  # bearish phase
]

values = ['recovery', 'accumulation', 'bullish', 'warning','distribution','bearish']
dfResult['MarketPhase'] = np.select(conditions, values)
# print(dfResult)

currentDate = date.today().strftime('%Y%m%d')
dfResult.to_csv("coinpairByMarketPhase_"+stablecoin+"_"+timeframe+"_"+currentDate+".csv")

# %%
dfRecovery = dfResult.query("MarketPhase == 'recovery'")
print("\nCoins in Recovery Market Phase")
print(dfRecovery)

dfAccumulation= dfResult.query("MarketPhase == 'accumulation'")
print("\nCoins in Accumulation Market Phase")
print(dfAccumulation)

dfBullish = dfResult.query("MarketPhase == 'bullish'")
print("\nCoins in Bullish Market Phase")
print(dfBullish)

dfWarning = dfResult.query("MarketPhase == 'warning'")
print("\nCoins in Warning Market Phase")
print(dfWarning)

dfDistribution = dfResult.query("MarketPhase == 'distribution'")
print("\nCoins in Distribution Market Phase")
print(dfDistribution)

dfBearish = dfResult.query("MarketPhase == 'bearish'")
print("\nCoins in Bearish Market Phase")
print(dfBearish)

# # get yesterday results and merge 
# # Yesterday date
# yesterdayDate = date.today() - timedelta(days = 1)
# # print("Yesterday was: ", yesterday.strftime('%Y%m%d'))
# yesterdayDate = yesterdayDate.strftime('%Y%m%d')
# dfResultYesterday = pd.read_csv("coinListByMarketPhases_"+stablecoin+"_"+timeframe+"_"+yesterdayDate+".csv")
# # filter by accumulation and bullish
# dfYesterdayAccumulation = dfResultYesterday.query("MarketPhase == 'accumulation'")
# dfYesterdayBullish = dfResultYesterday.query("MarketPhase == 'bullish'")

# pd.merge(dfBullish, dfYesterdayBullish, on="Coinpair", how="outer", indicator=True)

stop = timeit.default_timer()
print("END")
print('Execution Time (s): ', stop - start) 


