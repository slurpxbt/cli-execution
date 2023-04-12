from pybit.unified_trading import HTTP
import requests
import time
import pandas as pd
import json
from pathlib import Path


def get_credentials():
    root = Path(".")
    file_path = f"{root}/credentials.json"

    with open(file_path) as file:

        file = file.read()
        credentials = json.loads(file)

        api_key = credentials["bybit_api_key"]
        api_secret = credentials["bybit_secret_key"]

    return api_key, api_secret


def get_usdt_balances(client):

    try:
        balances = client.get_wallet_balance(accountType="CONTRACT")["result"]["list"][0]["coin"]
        usdt_balance = None
        for balance in balances:
            if balance["coin"] == "USDT":
                usdt_balance = balance

        if usdt_balance is not None:
            total_balance = round(float(usdt_balance["equity"]))

            print(f"total usdt balance: {total_balance} USDT")

            return total_balance
    except:
        print("Error with requesting USDT balances")
        total_balance = None


        return total_balance


def get_usdt_tickers(client):

    symbols = client.get_instruments_info(category="linear")["result"]["list"]
    tickers = {}
    for row in symbols:
        symbol = row["symbol"]
        ticker = row["symbol"]
        if "USDT" in symbol:

            symbol = symbol.replace("USDT", "")

            if "10000" in symbol:
                symbol = symbol.replace("10000", "")
            elif "1000" in symbol:
                symbol = symbol.replace("1000", "")

            tickers[symbol] = ticker

    return tickers


def get_last_price(client, ticker):
    ticker_data = client.get_tickers(category="linear", symbol=ticker)["result"]["list"][0]
    last_price = float(ticker_data["lastPrice"])
    return last_price


def get_instrument_info(client, ticker):
    instrument_info = client.get_instruments_info(category="linear", symbol=ticker)["result"]["list"][0]

    min_size = float(instrument_info["lotSizeFilter"]["minOrderQty"])
    max_size = float(instrument_info["lotSizeFilter"]["maxOrderQty"])
    decimals = str(min_size)[::-1].find('.')
    print(f"{ticker} | min: {min_size} coins | decimals: {decimals}")

    return max_size, min_size, decimals


# CLI inputs
def select_ticker(tickers):
    try:
        input_ticker = input("select ticker >>> ")
        ticker = tickers[input_ticker.upper()]
        print(f"{ticker} selected")
        return ticker
    except:
        print("Invalid ticker selected")
        return None


def select_order_amount():

    input_interval = input("select number of orders >>> ")
    try:
        input_interval = int(input_interval)
        return input_interval
    except:
        print("Error selecting number of orders: input must be number")
        return None


def select_usdt_size():
    input_size = input("select position size[usdt] >>> ")
    try:
        input_size = int(input_size)
        return input_size
    except:
        print("Error selecting positions size: input must be number")
        return None


def select_duration():
    input_duration = input("select duration minutes >>> ")
    try:
        input_duration = int(input_duration)
        return input_duration
    except:
        print("Error selecting positions size: input must be number")
        return None


def select_side():
    input_side = input("select side b=Buy, s=Sell >>> ")
    if input_side.lower() == "b":
        input_side = "Buy"
    elif input_side.lower() == "s":
        input_side = "Sell"
    else:
        print("Error with selecting side")
        input_side = None

    return input_side
# --------------------------------------------


# ORDER/POSITION OVERVIEW FUNCTIONS
def get_open_positions(client):
    positions = client.get_positions(category="linear", settleCoin="USDT")["result"]["list"]
    open_positions = {}
    counter = 0
    for position in positions:
        size = float(position["size"])

        if size > 0:
            open_positions[counter] = position
            counter += 1

    if open_positions:
        return open_positions
    else:
        print("No open positions")
        return open_positions


def display_positions(positions):
    print("Current positions")
    positions_df = pd.DataFrame.from_dict(positions, orient="index")
    positions_df = positions_df[["symbol", "side", "size", "positionValue", "avgPrice", "unrealisedPnl", "takeProfit", "stopLoss"]]
    print(positions_df.to_markdown())
    print("\n")


# ORDER EXECUTION functions
def market_order(client, tickers):
    """
    market order, it  uses short tvwap over 15seconds with 10 orders
    """
    ticker = select_ticker(tickers)
    side = select_side()                # buy/sell
    position_size = select_usdt_size()  # usd amount

    error = False
    if ticker is not None and side is not None and position_size is not None:
        last_price = get_last_price(client=client, ticker=ticker)
        max_size, min_size, decimals = get_instrument_info(client=client, ticker=ticker)

        order_amount = 10
        seconds = 15
        second_interval = seconds / order_amount

        total_coin_size = round(position_size / last_price * 0.995, decimals)
        if total_coin_size > max_size:
            print("Error: Exceded max position size")
            error = True

        order_size = round(total_coin_size / order_amount, decimals)
        if order_size < min_size:
            print("Error: ordes size below minimum size")
            error = True

        if not error:
            print(f"total size: {total_coin_size} coins")
            print(f"executing >>> {order_size} coins | each: {second_interval} seconds")

            prev_size = float(bybit_client.get_positions(category="linear", symbol=ticker)["result"]["list"][0]["size"])
            open_size = 0
            while open_size < total_coin_size:

                client.place_order(category="linear", symbol=ticker, side=side, orderType="Market", qty=round(order_size, decimals), timeInForce="IOC", reduceOnly=False)
                open_size = float(bybit_client.get_positions(category="linear", symbol=ticker)["result"]["list"][0]["size"]) - prev_size

                print(f"fast twap running >>> opened: {round(open_size, decimals)} coins | side: {side}")
                time.sleep(second_interval)

                if (open_size + order_size) > total_coin_size:
                    order_size = total_coin_size - open_size

                    if order_size < min_size:
                        print(f"remaining size to low >>> unfilled size: {order_size} coins")
                        break

            print("market order executed")
        else:
            print("Error occured")


def market_close(client):
    """
    market close order, it uses short tvwap over 15seconds with 10 orders
    """

    positions = get_open_positions(client=bybit_client)
    display_positions(positions)
    # print("Current positions")
    # for key, position in positions.items():
    #     print(f"id: {key} | {position['symbol']} | entry: {position['entry_price']} | side: {position['side']} | size: {position['size']} coins | pos value: {round(position['position_value'])} usd | pnl: {round(position['unrealised_pnl'])} usd")

    try:
        close_id = int(input("select ID of the position you wish to close >>> "))
    except:
        print("Error: ID must be number")

    if close_id in positions.keys():
        position = positions[close_id]
        ticker = position["symbol"]
        side = position["side"]
        size = float(position["size"])

        max_size, min_size, decimals = get_instrument_info(client=client, ticker=ticker)

        if side == "Buy":
            reduce_side = "Sell"
        elif side == "Sell":
            reduce_side = "Buy"

        order_amount = 10
        seconds = 15

        if (size / order_amount) > min_size:
            order_size = size / order_amount
            second_interval = seconds / order_amount

            open_size = float(bybit_client.get_positions(category="linear", symbol=ticker)["result"]["list"][0]["size"])
            while open_size > 0:

                client.place_order(category="linear", symbol=ticker, side=reduce_side, orderType="Market", qty=round(order_size, decimals), timeInForce="IOC", reduceOnly=True)
                open_size = float(bybit_client.get_positions(category="linear", symbol=ticker)["result"]["list"][0]["size"])

                print(f"fast twap running >>> size remaining: {open_size} coins | side: {reduce_side}")
                time.sleep(second_interval)

                if (open_size - order_size) < 0:
                    order_size = open_size

            print("market order executed")

        else:
            print("orders to smal, order amount halved")
            order_amount = 5
            order_size = size / order_amount
            second_interval = seconds / order_amount

            open_size = float(bybit_client.get_positions(category="linear", symbol=ticker)["result"]["list"][0]["size"])
            while open_size > 0:

                client.place_order(category="linear", symbol=ticker, side=reduce_side, orderType="Market", qty=round(order_size, decimals), timeInForce="IOC", reduceOnly=True)
                open_size = float(bybit_client.get_positions(category="linear", symbol=ticker)["result"]["list"][0]["size"])

                print(f"fast twap running >>> size remaining: {open_size} coins | side: {reduce_side}")
                time.sleep(second_interval)

                if (open_size - order_size) < 0:
                    order_size = open_size

            print("market order executed")

    else:
        print("Error: Wrong ID selected")


def basic_twap(client, tickers):
    """
    Basic linear: you specify, order number, position size, duration and side, position is then opened in linear fashion with same intervals and size per interval

    """
    ticker = select_ticker(tickers)
    order_amount = select_order_amount()   # number or orders
    position_size = select_usdt_size()  # usd amount
    twap_duration = select_duration()   # minutes
    side = select_side()                # buy/sell

    error = False
    if ticker is not None and order_amount is not None and position_size is not None and twap_duration is not None and side is not None:
        last_price = get_last_price(client=client, ticker=ticker)
        max_size, min_size, decimals = get_instrument_info(client=client, ticker=ticker)

        seconds = twap_duration * 60
        total_coin_size = round(position_size / last_price * 0.995, decimals)
        if total_coin_size > max_size:
            print("Error: Exceded max position size")
            error = True

        order_size = round(total_coin_size / order_amount, decimals)
        if order_size < min_size:
            print("Error: ordes size below minimum size")
            error = True

        second_interval = seconds / order_amount

        if not error:
            print(f"total size: {total_coin_size} coins")
            print(f"executing >>> {order_size} coins | each: {second_interval} seconds")

            prev_size = float(bybit_client.get_positions(category="linear", symbol=ticker)["result"]["list"][0]["size"])
            open_size = 0
            while open_size < total_coin_size:

                client.place_order(category="linear", symbol=ticker, side=side, orderType="Market", qty=round(order_size, decimals), timeInForce="IOC", reduceOnly=False)
                open_size = float(bybit_client.get_positions(category="linear", symbol=ticker)["result"]["list"][0]["size"]) - prev_size

                print(f"twap running >>> opened: {open_size} ETH | side: {side}")
                time.sleep(second_interval)

                if (open_size + order_size) > total_coin_size:
                    order_size = total_coin_size - open_size

                    if order_size < min_size:
                        print(f"remaining size to low >>> unfilled size: {order_size} coins")
                        break

            print("twap finished")
        else:
            print("Error occured")


def basic_twap_reduce(client):
    """
       Basic linear close: you specify, order number, duration and side, position is then opened in linear fashion with same intervals and size per interval

    """

    positions = get_open_positions(client=bybit_client)
    display_positions(positions)

    try:
        close_id = int(input("select ID of the position you wish to close >>> "))
    except:
        print("Error: ID must be number")

    order_amount = select_order_amount()  # number or orders
    twap_duration = select_duration()  # minutes

    if close_id in positions.keys():
        position = positions[close_id]
        ticker = position["symbol"]
        side = position["side"]
        size = float(position["size"])

        print(f"{ticker} position selected to close")
        max_size, min_size, decimals = get_instrument_info(client=client, ticker=ticker)
        seconds = twap_duration * 60

        if side == "Buy":
            reduce_side = "Sell"
        elif side == "Sell":
            reduce_side = "Buy"

        error = False
        if order_amount is not None and twap_duration is not None:

            order_size = size / order_amount
            second_interval = seconds / order_amount

            if order_size < min_size:
                print("Error: ordes size below minimum size")
                error = True

            if not error:
                open_size = float(bybit_client.get_positions(category="linear", symbol=ticker)["result"]["list"][0]["size"])
                while open_size > 0:

                    client.place_order(category="linear", symbol=ticker, side=reduce_side, orderType="Market", qty=round(order_size, decimals), timeInForce="IOC", reduceOnly=True)
                    open_size = float(bybit_client.get_positions(category="linear", symbol=ticker)["result"]["list"][0]["size"])

                    print(f"fast twap running >>> size remaining: {open_size} coins | side: {reduce_side}")
                    time.sleep(second_interval)

                    if (open_size - order_size) < 0:
                        order_size = open_size

                print("twap finished")

    else:
        print("Error: Wrong ID selected")
# --------------------------------------------



api_key, api_secret = get_credentials()
bybit_client = HTTP(testnet=False, api_key=api_key, api_secret=api_secret)
get_usdt_balances(bybit_client)
usdt_tickers = get_usdt_tickers(bybit_client)
open_positions = get_open_positions(client=bybit_client)
display_positions(open_positions)


# basic_twap(client=bybit_client, tickers=usdt_tickers)
# basic_twap_reduce(client=bybit_client)

# market_order(client=bybit_client, tickers=usdt_tickers)
# market_close(client=bybit_client)



