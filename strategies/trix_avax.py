import sys
sys.path.append('./CryptoTradingBot')
from utilities.spot_ftx import SpotFtx
from utilities.conf_loader import ConfLoader
from utilities.bot_logging import BotLogging
import ta
import json
from datetime import datetime
import pandas_ta as pda

now = datetime.now()
log_prefix = 'TRIX AVAX [' + now.strftime("%d-%m-%Y %H:%M:%S") + ']'

with open('./CryptoTradingBot/config/config.json', 'r') as fconfig:
    configJson = json.load(fconfig)
    config = ConfLoader(configJson)

logger = BotLogging(
    config.strategies.TrixAVAX.slack.url,
    config.strategies.TrixAVAX.slack.username,
    config.strategies.TrixAVAX.slack.channel
)

ftx = SpotFtx(
    apiKey=config.strategies.TrixAVAX.apiKey,
    secret=config.strategies.TrixAVAX.secret,
    subAccountName=config.strategies.TrixAVAX.subAccountName
)

timeframe = '1h'
fiatSymbol = 'USDT'
cryptoSymbol = 'AVAX'
pair = 'AVAX/USDT'
minTokenForSell = 0.1
minUsdForBuy = 50

# -- Hyper parameters --
stochOverBought = 0.85
stochOverSold = 0.2
trixLength = 9
trixSignal = 21

df = ftx.get_last_historical(pair, timeframe, 100)

df['TRIX'] = ta.trend.ema_indicator(ta.trend.ema_indicator(ta.trend.ema_indicator(close=df['close'], window=trixLength), window=trixLength), window=trixLength)
df['TRIX_PCT'] = df["TRIX"].pct_change()*100
df['TRIX_SIGNAL'] = ta.trend.sma_indicator(df['TRIX_PCT'], trixSignal)
df['TRIX_HISTO'] = df['TRIX_PCT'] - df['TRIX_SIGNAL']
df['STOCH_RSI'] = ta.momentum.stochrsi(close=df['close'], window=14, smooth1=3, smooth2=3)

coinBalance = ftx.get_all_balance()
coinInUsd = ftx.get_all_balance_in_usd()
actualPrice = df['close'].iloc[-1]

def buyCondition(row):
    if row['TRIX_HISTO'] > 0 and row['STOCH_RSI'] < stochOverBought:
        return True
    else:
        return False

def sellCondition(row):
    if row['TRIX_HISTO'] < 0 and row['STOCH_RSI'] > stochOverSold:
        return True
    else:
        return False

print(log_prefix + ' => coin price :' + str(actualPrice) + '$, usd balance : ' + str(coinInUsd) + '$, coin balance : ' + str(coinBalance))

if buyCondition(df.iloc[-2]):
    usdBalance = ftx.get_balance_of_one_coin('USDT')
    if float(usdBalance) > minUsdForBuy:
        buyPrice = float(ftx.convert_price_to_precision(pair, ftx.get_bid_ask_price(pair)['ask']))
        buyAmount = ftx.convert_amount_to_precision(pair, usdBalance / buyPrice)
        buy = ftx.place_market_order(pair, 'buy', buyAmount)
        print(log_prefix + " => BUY " + cryptoSymbol + ' at ' + str(actualPrice) + "$")
        logger.send_message(log_prefix + " => BUY " + cryptoSymbol + ' at ' + str(actualPrice) + "$")
    else:
        print(log_prefix + " => If you give me more USD I will buy more " + cryptoSymbol)

elif sellCondition(df.iloc[-2]):
    avaxBalance = ftx.get_balance_of_one_coin('AVAX')
    if float(avaxBalance) > minTokenForSell:
        sell = ftx.place_market_order(pair, 'sell', avaxBalance)
        print(log_prefix + " => SELL" + cryptoSymbol + ' at ' + str(actualPrice) + "$")
        logger.send_message(log_prefix + " => SELL" + cryptoSymbol + ' at ' + str(actualPrice) + "$")
    else:
        print(log_prefix + " => If you give me more " + cryptoSymbol + " I will sell it")
else :
    print(log_prefix + " => No opportunity to take")
