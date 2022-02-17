import sys
sys.path.append('./CryptoTradingBot')
from utilities.spot_ftx import SpotFtx
from utilities.conf_loader import ConfLoader
from utilities.bot_logging import BotLogging
import ta
import json
from datetime import datetime
import time

with open('./CryptoTradingBot/config/config.json', 'r') as fconfig:
    configJson = json.load(fconfig)
    config = ConfLoader(configJson)

with open('./CryptoTradingBot/config/pair_list.json', 'r') as fpairJson:
    pairJson = json.load(fpairJson)
    fpairJson.close()

logger = BotLogging(
    config.strategies.alligator.slack.url,
    config.strategies.alligator.slack.username,
    config.strategies.alligator.slack.channel
)

ftx = SpotFtx(
    apiKey=config.strategies.alligator.apiKey,
    secret=config.strategies.alligator.secret,
    subAccountName=config.strategies.alligator.subAccountName
)

now = datetime.now()
log_prefix = 'ALLIGATOR MULTICOIN [' + now.strftime("%d-%m-%Y %H:%M:%S") + ']'

timeframe = '1h'
pairList = pairJson['ftxClassicPair']

# -- Indicator variable --
stochWindow = 14
willWindow = 14

# -- Hyper parameters --
maxOpenPosition = 5
stochOverBought = 0.82
stochOverSold = 0.25
TpPct = 0.15

dfList = {}
for pair in pairList:
    df = ftx.get_last_historical(pair, timeframe, 210)
    dfList[pair.replace('/USDT', '')] = df

for coin in dfList:
    # -- Drop all columns we do not need --
    dfList[coin].drop(columns=dfList[coin].columns.difference(['open', 'high', 'low', 'close', 'volume']), inplace=True)

    # -- Indicators, you can edit every value --

    dfList[coin]['EMA1'] = ta.trend.ema_indicator(close=dfList[coin]['close'], window=7)
    dfList[coin]['EMA2'] = ta.trend.ema_indicator(close=dfList[coin]['close'], window=30)
    dfList[coin]['EMA3'] = ta.trend.ema_indicator(close=dfList[coin]['close'], window=50)
    dfList[coin]['EMA4'] = ta.trend.ema_indicator(close=dfList[coin]['close'], window=100)
    dfList[coin]['EMA5'] = ta.trend.ema_indicator(close=dfList[coin]['close'], window=121)
    dfList[coin]['EMA6'] = ta.trend.ema_indicator(close=dfList[coin]['close'], window=200)

    dfList[coin]['STOCH_RSI'] = ta.momentum.stochrsi(close=dfList[coin]['close'], window=stochWindow, smooth1=3,
                                                     smooth2=3)
    dfList[coin]['WillR'] = ta.momentum.williams_r(high=dfList[coin]['high'], low=dfList[coin]['low'],
                                                   close=dfList[coin]['close'], lbp=willWindow)

# -- Condition to BUY market --
def buyCondition(row, previousRow=None):
    if row['EMA1'] > row['EMA2'] and row['EMA2'] > row['EMA3'] and row['EMA3'] > row['EMA4'] and row['EMA4'] > row['EMA5'] and row['EMA5'] > row['EMA6'] and row['STOCH_RSI'] < stochOverBought:
        return True
    else:
        return False


# -- Condition to SELL market --
def sellCondition(row, previousRow=None):
    if row['EMA2'] > row['EMA1'] and row['STOCH_RSI'] > stochOverSold:
        return True
    else:
        return False


coinBalance = ftx.get_all_balance()
coinInUsd = ftx.get_all_balance_in_usd()
usdBalance = coinBalance['USDT']
del coinBalance['USDT']
del coinInUsd['USDT']
totalBalanceInUsd = usdBalance + sum(coinInUsd.values())
coinPositionList = []
for coin in coinInUsd:
    if coinInUsd[coin] > 0.05 * totalBalanceInUsd:
        coinPositionList.append(coin)
openPositions = len(coinPositionList)

# Sell
for coin in coinPositionList:
    if sellCondition(dfList[coin].iloc[-1]) == True:
        openPositions -= 1
        symbol = coin + '/USDT'
        # cancel = ftx.cancel_all_open_order(symbol)
        # time.sleep(1)
        sell = ftx.place_market_order(symbol, 'sell', coinBalance[coin])
        print(log_prefix + " Sell " + coin)
        logger.send_message(log_prefix + " Sell " + coin)
# Buy
if openPositions < maxOpenPosition:
    for coin in dfList:
        if coin not in coinPositionList:
            if buyCondition(dfList[coin].iloc[-1]) == True and openPositions < maxOpenPosition:
                time.sleep(1)
                usdBalance = ftx.get_balance_of_one_coin('USDT')
                symbol = coin + '/USDT'

                buyPrice = float(ftx.convert_price_to_precision(symbol, ftx.get_bid_ask_price(symbol)['ask']))
                tpPrice = float(ftx.convert_price_to_precision(symbol, buyPrice + TpPct * buyPrice))
                buyQuantityInUsd = usdBalance * 1 / (maxOpenPosition - openPositions)

                if openPositions == maxOpenPosition - 1:
                    buyQuantityInUsd = 0.95 * buyQuantityInUsd

                buyAmount = ftx.convert_amount_to_precision(symbol, buyQuantityInUsd / buyPrice)

                buy = ftx.place_market_order(symbol, 'buy', buyAmount)
                print(log_prefix + " Buy " + str(buyAmount) + coin + " at " + str(buyPrice) + " $")
                logger.send_message(log_prefix + " Buy " + str(buyAmount) + coin + " at " + str(buyPrice) + " $")
                if config.strategies.alligator.options.tpEnabled:
                    time.sleep(2)
                    tp = ftx.place_limit_order(symbol, 'sell', buyAmount, tpPrice)
                    try:
                        tp["id"]
                    except:
                        time.sleep(2)
                        tp = ftx.place_limit_order(symbol, 'sell', buyAmount, tpPrice)
                        pass
                    # print("Place", buyAmount, coin, "TP at", tpPrice, tp)

                openPositions += 1
            else:
                print(log_prefix + " " + coin + " No buy condition")