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
log_prefix = 'SUPERTREND BTC [' + now.strftime("%d-%m-%Y %H:%M:%S") + ']'

with open('./CryptoTradingBot/config/config.json', 'r') as fconfig:
    configJson = json.load(fconfig)
    config = ConfLoader(configJson)

logger = BotLogging(
    config.strategies.superTrendBTC.slack.url,
    config.strategies.superTrendBTC.slack.username,
    config.strategies.superTrendBTC.slack.channel
)

ftx = SpotFtx(
    apiKey=config.strategies.superTrendBTC.apiKey,
    secret=config.strategies.superTrendBTC.secret,
    subAccountName=config.strategies.superTrendBTC.subAccountName
)

timeframe = '1h'
fiatSymbol = 'USDT'
cryptoSymbol = 'BTC'
pair = 'BTC/USDT'
minTokenForSell = 0.01
minUsdForBuy = 50

# -- Hyper parameters --
stochOverBought = 0.88
stochOverSold = 0.25

df = ftx.get_last_historical(pair, timeframe, 210)

df['EMA90'] = ta.trend.ema_indicator(df['close'], 90)
df['STOCH_RSI'] = ta.momentum.stochrsi(df['close'])

ST_length = 21
ST_multiplier = 3.0
superTrend = pda.supertrend(df['high'], df['low'], df['close'], length=ST_length, multiplier=ST_multiplier)
df['SUPER_TREND'] = superTrend['SUPERT_'+str(ST_length)+"_"+str(ST_multiplier)]
df['SUPER_TREND_DIRECTION1'] = superTrend['SUPERTd_'+str(ST_length)+"_"+str(ST_multiplier)]

ST_length = 19
ST_multiplier = 4.0
superTrend = pda.supertrend(df['high'], df['low'], df['close'], length=ST_length, multiplier=ST_multiplier)
df['SUPER_TREND'] = superTrend['SUPERT_'+str(ST_length)+"_"+str(ST_multiplier)]
df['SUPER_TREND_DIRECTION2'] = superTrend['SUPERTd_'+str(ST_length)+"_"+str(ST_multiplier)]

ST_length = 47
ST_multiplier = 7.0
superTrend = pda.supertrend(df['high'], df['low'], df['close'], length=ST_length, multiplier=ST_multiplier)
df['SUPER_TREND'] = superTrend['SUPERT_'+str(ST_length)+"_"+str(ST_multiplier)]
df['SUPER_TREND_DIRECTION3'] = superTrend['SUPERTd_'+str(ST_length)+"_"+str(ST_multiplier)]

coinBalance = ftx.get_all_balance()
coinInUsd = ftx.get_all_balance_in_usd()
actualPrice = df['close'].iloc[-1]

# -- Condition to BUY market --
def buyCondition(row):
    if row['SUPER_TREND_DIRECTION1'] + row['SUPER_TREND_DIRECTION2'] + row['SUPER_TREND_DIRECTION3'] >= 1 and row['close'] > row['EMA90'] and row['STOCH_RSI'] < stochOverBought:
        return True
    else:
        return False


# -- Condition to SELL market --
def sellCondition(row):
    if row['SUPER_TREND_DIRECTION1'] + row['SUPER_TREND_DIRECTION2'] + row['SUPER_TREND_DIRECTION3'] < 1:
        return True
    else:
        return False

print(log_prefix + ' => coin price :' + str(actualPrice) + '$, usd balance : ' + str(coinInUsd) + '$, coin balance : ' + str(coinBalance))

if buyCondition(df.iloc[-2]) == True:
    usdBalance = ftx.get_balance_of_one_coin('USDT')
    if float(usdBalance) > minUsdForBuy:
        buyPrice = float(ftx.convert_price_to_precision(pair, ftx.get_bid_ask_price(pair)['ask']))
        buyAmount = ftx.convert_amount_to_precision(pair, usdBalance / buyPrice)
        buy = ftx.place_market_order(pair, 'buy', buyAmount)
        print(log_prefix + " => BUY " + cryptoSymbol + ' at ' + str(actualPrice) + "$")
        logger.send_message(log_prefix + " => BUY " + cryptoSymbol + ' at ' + str(actualPrice) + "$")
    else:
        print(log_prefix + " => If you give me more USD I will buy more " + cryptoSymbol)

elif sellCondition(df.iloc[-2]) == True:
    btcBalance = ftx.get_balance_of_one_coin('BTC')
    if float(btcBalance) > minTokenForSell:
        sell = ftx.place_market_order(pair, 'sell', btcBalance)
        print(log_prefix + " => SELL" + cryptoSymbol + ' at ' + str(actualPrice) + "$")
        logger.send_message(log_prefix + " => SELL " + cryptoSymbol + ' at ' + str(actualPrice) + "$")
    else:
        print(log_prefix + " => If you give me more " + cryptoSymbol + " I will sell it")
else :
  print(log_prefix + " => No opportunity to take")
