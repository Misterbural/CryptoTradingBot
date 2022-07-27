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

# Constant
timeframe = '1h'
fiatSymbol = 'USDT'
cryptoSymbol = 'ETH'
pair = 'ETH/USDT'
minUsdForBuy = 50
btcToKeep = 0.42149381
btcMarge = 0.01
ethToKeep = 4.24305096
ethMarge = 0.1

# -- Set indicators --
df = ftx.get_last_historical(pair, timeframe, 1000)

df['EMA95'] = ta.trend.ema_indicator(df['close'], 95)

ST_length = 11
ST_multiplier = 3.0
superTrend = pda.supertrend(df['high'], df['low'], df['close'], length=ST_length, multiplier=ST_multiplier)
df['SUPER_TREND'] = superTrend['SUPERT_'+str(ST_length)+"_"+str(ST_multiplier)]
df['SUPER_TREND_DIRECTION1'] = superTrend['SUPERTd_'+str(ST_length)+"_"+str(ST_multiplier)]

ST_length = 22
ST_multiplier = 4.0
superTrend = pda.supertrend(df['high'], df['low'], df['close'], length=ST_length, multiplier=ST_multiplier)
df['SUPER_TREND'] = superTrend['SUPERT_'+str(ST_length)+"_"+str(ST_multiplier)]
df['SUPER_TREND_DIRECTION2'] = superTrend['SUPERTd_'+str(ST_length)+"_"+str(ST_multiplier)]

ST_length = 64
ST_multiplier = 8.0
superTrend = pda.supertrend(df['high'], df['low'], df['close'], length=ST_length, multiplier=ST_multiplier)
df['SUPER_TREND'] = superTrend['SUPERT_'+str(ST_length)+"_"+str(ST_multiplier)]
df['SUPER_TREND_DIRECTION3'] = superTrend['SUPERTd_'+str(ST_length)+"_"+str(ST_multiplier)]

print(log_prefix + ' Last candle complete load ' + str(df.iloc[-2]))

# -- Condition to BUY market --
def buyCondition(row):
    if row['SUPER_TREND_DIRECTION1'] + row['SUPER_TREND_DIRECTION2'] + row['SUPER_TREND_DIRECTION3'] >= 1 and row['close'] > row['EMA95']:
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
usdBalance = ftx.get_balance_of_one_coin('USDT')

# Check market conditions
if buyCondition(df.iloc[-2]) == True:
    if float(usdBalance) > minUsdForBuy and float(ethBalance) < ethToKeep + ethMarge:
        buyPrice = float(ftx.convert_price_to_precision(pair, ftx.get_bid_ask_price(pair)['ask']))
        buyAmount = ftx.convert_amount_to_precision(pair, usdBalance / buyPrice)
        if btcBalance < btcToKeep + btcMarge:
            buyAmount = ftx.convert_amount_to_precision(pair, (usdBalance / 100 * 55) / buyPrice)
        buy = ftx.place_market_order(pair, 'buy', buyAmount)
        print(log_prefix + " => BUY " + cryptoSymbol + ' at ' + str(buyPrice) + "$")
        logger.send_message(log_prefix + " => BUY " + cryptoSymbol + ' at ' + str(buyPrice) + "$")
    else:
        print(log_prefix + " => If you give me more USD I will buy more " + cryptoSymbol)

elif sellCondition(df.iloc[-2]) == True:
    if float(ethBalance) > ethToKeep + ethMarge:
        sellPrice = float(ftx.convert_price_to_precision(pair, ftx.get_bid_ask_price(pair)['bid']))
        quantityTotoSell = ethBalance - ethToKeep
        sell = ftx.place_market_order(pair, 'sell', quantityTotoSell)
        print(log_prefix + " => SELL" + cryptoSymbol + ' at ' + str(sellPrice) + "$")
        logger.send_message(log_prefix + " => SELL " + cryptoSymbol + ' at ' + str(sellPrice) + "$")
    else:
        print(log_prefix + " => If you give me more " + cryptoSymbol + " I will sell it")
else :
  print(log_prefix + " => No opportunity to take")
