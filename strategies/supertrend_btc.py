import sys
sys.path.append('./CryptoTradingBot')
from utilities.spot_ftx import SpotFtx
from utilities.conf_loader import ConfLoader
from utilities.bot_logging import BotLogging
import ta
import json
from datetime import datetime
import pandas_ta as pda
import time

now = datetime.now()
log_prefix = 'SUPERTREND BTC [' + now.strftime("%d-%m-%Y %H:%M:%S") + ']'

# Config
with open('./CryptoTradingBot/config/config.json', 'r') as fconfig:
    configJson = json.load(fconfig)
    config = ConfLoader(configJson)

logger = BotLogging(
    config.strategies.mainAccount.slack.url,
    config.strategies.mainAccount.slack.username,
    config.strategies.mainAccount.slack.channel
)

ftx = SpotFtx(
    apiKey=config.strategies.mainAccount.apiKey,
    secret=config.strategies.mainAccount.secret
)

# Add sleep to avoid problem with parallel process
time.sleep(6)

# Constant
timeframe = '1h'
fiatSymbol = 'USDT'
cryptoSymbol = 'BTC'
pair = 'BTC/USDT'
minUsdForBuy = 50
btcToKeep = 0.42175796
btcMarge = 0.01
ethToKeep = 4.24594127
ethMarge = 0.1
avaxToKeep = 50
avaxMarge = 1

# -- Set indicators --
# stochOverBought = 0.88
df = ftx.get_last_historical(pair, timeframe, 1000)

df['EMA80'] = ta.trend.ema_indicator(df['close'], 80)

ST_length = 17
ST_multiplier = 3.0
superTrend = pda.supertrend(df['high'], df['low'], df['close'], length=ST_length, multiplier=ST_multiplier)
df['SUPER_TREND'] = superTrend['SUPERT_'+str(ST_length)+"_"+str(ST_multiplier)]
df['SUPER_TREND_DIRECTION1'] = superTrend['SUPERTd_'+str(ST_length)+"_"+str(ST_multiplier)]

ST_length = 12
ST_multiplier = 4.0
superTrend = pda.supertrend(df['high'], df['low'], df['close'], length=ST_length, multiplier=ST_multiplier)
df['SUPER_TREND'] = superTrend['SUPERT_'+str(ST_length)+"_"+str(ST_multiplier)]
df['SUPER_TREND_DIRECTION2'] = superTrend['SUPERTd_'+str(ST_length)+"_"+str(ST_multiplier)]

ST_length = 41
ST_multiplier = 7.0
superTrend = pda.supertrend(df['high'], df['low'], df['close'], length=ST_length, multiplier=ST_multiplier)
df['SUPER_TREND'] = superTrend['SUPERT_'+str(ST_length)+"_"+str(ST_multiplier)]
df['SUPER_TREND_DIRECTION3'] = superTrend['SUPERTd_'+str(ST_length)+"_"+str(ST_multiplier)]

print(log_prefix + ' Last candle complete load ' + str(df.iloc[-2]))

# -- Condition to BUY market --
def buyCondition(row):
    if row['SUPER_TREND_DIRECTION1'] + row['SUPER_TREND_DIRECTION2'] + row['SUPER_TREND_DIRECTION3'] >= 1 and row['close'] > row['EMA80']:
        return True
    else:
        return False


# -- Condition to SELL market --
def sellCondition(row):
    if row['SUPER_TREND_DIRECTION1'] + row['SUPER_TREND_DIRECTION2'] + row['SUPER_TREND_DIRECTION3'] < 1:
        return True
    else:
        return False

btcBalance = ftx.get_balance_of_one_coin('BTC')
ethBalance = ftx.get_balance_of_one_coin('ETH')
avaxBalance = ftx.get_balance_of_one_coin('AVAX')
usdBalance = ftx.get_balance_of_one_coin('USDT')

# Check market conditions
if buyCondition(df.iloc[-2]) == True:
    if float(usdBalance) > minUsdForBuy and float(btcBalance) < btcMarge:
        buyPrice = float(ftx.convert_price_to_precision(pair, ftx.get_bid_ask_price(pair)['ask']))
        buyAmount = ftx.convert_amount_to_precision(pair, usdBalance / buyPrice)
        if avaxBalance < avaxMarge and ethBalance < ethMarge :
            buyAmount = ftx.convert_amount_to_precision(pair, (usdBalance / 100 * 40) / buyPrice)
        elif avaxBalance > avaxMarge and ethBalance < ethMarge :
            buyAmount = ftx.convert_amount_to_precision(pair, (usdBalance / 100 * 45) / buyPrice)
        elif avaxBalance < avaxMarge and ethBalance > ethMarge :
            buyAmount = ftx.convert_amount_to_precision(pair, (usdBalance / 100 * 80) / buyPrice)
        buy = ftx.place_market_order(pair, 'buy', buyAmount)
        print(log_prefix + " => BUY " + cryptoSymbol + ' at ' + str(buyPrice) + "$")
        logger.send_message(log_prefix + " => BUY " + cryptoSymbol + ' at ' + str(buyPrice) + "$")
    else:
        print(log_prefix + " => If you give me more USD I will buy more " + cryptoSymbol)

elif sellCondition(df.iloc[-2]) == True:
    if float(btcBalance) > btcMarge:
        sellPrice = float(ftx.convert_price_to_precision(pair, ftx.get_bid_ask_price(pair)['bid']))
        quantityTotoSell = btcBalance
        sell = ftx.place_market_order(pair, 'sell', quantityTotoSell)
        print(log_prefix + " => SELL" + cryptoSymbol + ' at ' + str(sellPrice) + "$")
        logger.send_message(log_prefix + " => SELL " + cryptoSymbol + ' at ' + str(sellPrice) + "$")
    else:
        print(log_prefix + " => If you give me more " + cryptoSymbol + " I will sell it")
else :
  print(log_prefix + " => No opportunity to take")
