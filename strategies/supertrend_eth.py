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
log_prefix = 'SUPERTREND ETH [' + now.strftime("%d-%m-%Y %H:%M:%S") + ']'

with open('./CryptoTradingBot/config/config.json', 'r') as fconfig:
    configJson = json.load(fconfig)
    config = ConfLoader(configJson)

logger = BotLogging(
    config.strategies.superTrendETH.slack.url,
    config.strategies.superTrendETH.slack.username,
    config.strategies.superTrendETH.slack.channel
)

ftx = SpotFtx(
    apiKey=config.strategies.superTrendETH.apiKey,
    secret=config.strategies.superTrendETH.secret,
    subAccountName=config.strategies.superTrendETH.subAccountName
)

timeframe = '1h'
fiatSymbol = 'USDT'
cryptoSymbol = 'ETH'
pair = 'ETH/USDT'
minTokenForSell = 0.01
minUsdForBuy = 50

# -- Hyper parameters --
stochOverBought = 0.82
stochOverSold = 0.25

df = ftx.get_last_historical(pair, timeframe, 100)

df['EMA90']=ta.trend.ema_indicator(df['close'], 90)
df['STOCH_RSI']=ta.momentum.stochrsi(df['close'])

ST_length = 20
ST_multiplier = 3.0
superTrend = pda.supertrend(df['high'], df['low'], df['close'], length=ST_length, multiplier=ST_multiplier)
df['SUPER_TREND'] = superTrend['SUPERT_'+str(ST_length)+"_"+str(ST_multiplier)]
df['SUPER_TREND_DIRECTION1'] = superTrend['SUPERTd_'+str(ST_length)+"_"+str(ST_multiplier)]

ST_length = 20
ST_multiplier = 4.0
superTrend = pda.supertrend(df['high'], df['low'], df['close'], length=ST_length, multiplier=ST_multiplier)
df['SUPER_TREND'] = superTrend['SUPERT_'+str(ST_length)+"_"+str(ST_multiplier)]
df['SUPER_TREND_DIRECTION2'] = superTrend['SUPERTd_'+str(ST_length)+"_"+str(ST_multiplier)]

ST_length = 40
ST_multiplier = 8.0
superTrend = pda.supertrend(df['high'], df['low'], df['close'], length=ST_length, multiplier=ST_multiplier)
df['SUPER_TREND'] = superTrend['SUPERT_'+str(ST_length)+"_"+str(ST_multiplier)]
df['SUPER_TREND_DIRECTION3'] = superTrend['SUPERTd_'+str(ST_length)+"_"+str(ST_multiplier)]

coinBalance = ftx.get_all_balance()
coinInUsd = ftx.get_all_balance_in_usd()
actualPrice = df['close'].iloc[-1]

# -- Condition to BUY market --
def buyCondition(row):
    if row['SUPER_TREND_DIRECTION1'] + row['SUPER_TREND_DIRECTION2'] + row['SUPER_TREND_DIRECTION3'] >= 1 and row['close'] > row['EMA90']:
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
    ethBalance = ftx.get_balance_of_one_coin('BTC')
    if float(ethBalance) > minTokenForSell:
        sell = ftx.place_market_order(pair, 'sell', ethBalance)
        print(log_prefix + " => SELL" + cryptoSymbol + ' at ' + str(actualPrice) + "$")
        logger.send_message(log_prefix + " => SELL " + cryptoSymbol + ' at ' + str(actualPrice) + "$")
    else:
        print(log_prefix + " => If you give me more " + cryptoSymbol + " I will sell it")
else :
  print(log_prefix + " => No opportunity to take")
